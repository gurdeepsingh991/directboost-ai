import os, re, json, uuid
from typing import Dict, Any, List
from openai import OpenAI
from app.config import HF_API_TOKEN, ASSETS,ROOM_LETTER_TIER, AMENITY_LABELS, ROOM_TIER_FRIENDLY,MEAL_FRIENDLY,AMENITY_SLOGANS, SAFE_KEYS_OFFER, SAFE_KEYS_HISTORY, MONTH_NAME_TO_NUM, MONTH_NAMES,PROMPTS, TEMPLATES
from app.db.supabase_client import supabase

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=HF_API_TOKEN  
)

def get_discount_ofers(email: str, months: list[int] | None, year: int):
    """
    Fetch active discount_offers for a user, filtered by target_year and (optionally) months.
    `months` is a list of integers (1..12). In DB, target_month is a string like 'January'.
    """
    try:
        # 1) Resolve user
        user_res = supabase.table("users").select("user_id").eq("email", email).execute()
        if not user_res.data:
            return {"success": False, "message": f"No user found with email: {email}"}

        user_id = user_res.data[0]["user_id"]

        # 2) Build query (year + active); add month filter if provided
        query = (
            supabase.table("discount_offers")
            .select("*")                     # <- use string, not {"*"}
            .eq("user_id", user_id)
            .eq("target_year", year)
            .eq("is_active", True)
        )

        month_names = month_nums_to_names(months or [])
        if month_names:                      # only filter if caller passed months
            query = query.in_("target_month", month_names)

        resp = query.execute()
        discount_offers = resp.data or []

        # 3) If nothing, still return success w/ empty list (caller can handle)
        if not discount_offers:
            return {"success": True, "offers": [], "history": []}

        # 4) Fetch booking history for those with booking_id
        booking_ids = [o["booking_id"] for o in discount_offers if o.get("booking_id")]
        history_rows = []
        if booking_ids:
            hres = supabase.table("booking_history").select("*").in_("id", booking_ids).execute()
            history_rows = hres.data or []

        return {"success": True, "offers": discount_offers, "history": history_rows, "user_id": user_id}

    except Exception as e:
        return {"success": False, "message": f"Error fetching discount offers: {str(e)}"}

def get_email_from_api(offer: Dict[str, Any]) -> Dict[str, str]:
    """Call OpenRouter to generate a structured EmailPlan JSON (no PII)."""
    history_context = build_history_context(offer.get("history"))

    # context values (numeric discount, array perks)
    discount_pct = float(offer.get("discount_pct") or 0)
    perks_list = offer.get("perks") or []

    base_prompt = PROMPTS.get("email_generation")
    if not base_prompt:
        raise ValueError("System prompt 'email_generation' not found in DB")

    # Expect the DB prompt to include optional history_heading/history_pitch and the rules we discussed
    prompt = base_prompt.format(
        segment=offer.get("business_label"),
        hotel=offer.get("hotel"),
        room_name=friendly_room_name(offer.get("room_type"), offer.get("hotel")),
        stay=f"{offer.get('target_month')} {offer.get('target_year')}",
        discount_pct=int(discount_pct),   # numeric, no %
        perks=perks_list,                 # array
        history=history_context,
    )

    resp = client.chat.completions.create(
        model="meta-llama/llama-3-8b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=380
    )
    raw = resp.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except Exception as e:
        print("Primary JSON parse failed:", e)
        cleaned = extract_json(raw)
        return json.loads(cleaned)


def fine_tune_agent(plan: Dict[str, str]) -> Dict[str, str]:
    """Optional second pass to refine style."""
    return plan

def render_html_with_email(plan: Dict[str, str], offer: Dict[str, Any]) -> Dict[str, Any]:
    imgs = select_images_for_offer(offer)
    hero_img = offer.get("hero_image_url") or imgs["hero_image_url"]
    room_img = imgs["room_image_url"]

    # Complimentary perks (visuals) and previously-used amenities
    amenity_imgs = imgs["amenity_images"]                        # freebies
    history_amenity_imgs = imgs.get("history_amenity_images", [])  # NOT freebies

    # Links
    coupon = str(uuid.uuid4())[:8].upper()
    cta_url  = f"https://example.com/book?m={offer['target_month']}&y={offer['target_year']}&rt={offer['room_type']}&c={coupon}"
    unsub_url = f"https://example.com/unsub?u={offer.get('user_id','0')}"
    view_url  = f"https://example.com/view?m={offer['target_month']}&y={offer['target_year']}"

    # Discount / Perk emphasis
    discount = float(offer.get("discount_pct") or 0)
    has_discount = discount > 0
    has_perks = bool(offer.get("perks")) and len(amenity_imgs) > 0

    # Friendly room name (tier → label)
    room_tier = imgs.get("room_tier") or "standard"
    room_name = ROOM_TIER_FRIENDLY.get(room_tier, room_tier.title())

    # Meal shown only if actually complimentary
    meal_is_free = any((map_amenity_name(p) == "meal") for p in (offer.get("perks") or []))
    meal_name = MEAL_FRIENDLY.get((offer.get("meal") or "").upper(), "") if meal_is_free else ""

    month = offer.get("target_month", "")
    year  = offer.get("target_year", "")

    # ---- Normalize plan copy so we never leak placeholders or "0%" ----
    plan = {**plan}  # avoid mutating caller

    # Subject / preheader fallbacks
    if not plan.get("subject"):
        plan["subject"] = (
            f"{int(discount)}% OFF • {room_name} • {month} {year}" if has_discount
            else (f"Complimentary {humanize_perks(offer.get('perks'))} • {room_name} • {month} {year}" if has_perks
                  else f"{room_name} • {month} {year}")
        )
    if not plan.get("preheader"):
        plan["preheader"] = (
            f"Save {int(discount)}% on your next stay at {offer.get('hotel','our hotel')}."
            if has_discount else
            (f"Enjoy complimentary {humanize_perks(offer.get('perks'))} on us." if has_perks
             else f"Plan your {month} {year} stay with us.")
        )

    # Greeting must keep {{first_name}}
    plan.setdefault("greeting", "Dear {{first_name}},")

    # Offer line: discount-first, else perks, else neutral — NEVER print 0%
    nights_text = plural_nights(offer.get("offer_days"))
    if has_discount:
        core = f"Book your {room_name} for {month} {year}"
        if nights_text: core += f" and stay for {nights_text}"
        plan["offer_line"] = plan.get("offer_line") or f"{core} to enjoy an exclusive {int(discount)}% off."
    else:
        if has_perks:
            core = f"Book your {room_name} for {month} {year}"
            if nights_text: core += f" and stay for {nights_text}"
            plan["offer_line"] = plan.get("offer_line") or f"{core} and enjoy complimentary {humanize_perks(offer.get('perks'))}."
        else:
            plan["offer_line"] = plan.get("offer_line") or f"Book your {room_name} for {month} {year}."

    # ----- Complimentary section copy -----
    if has_perks:
        amenities_heading = plan.get("amenities_heading") or "Your Complimentary Perks"
        perks_pitch = plan.get("perks_pitch") or plan.get("perks_line") or "Enjoy a few extras on us."
    else:
        amenities_heading = ""
        perks_pitch = ""

    # ----- Previously-enjoyed section logic (dynamic + compact when both exist) -----
    perk_keys = set(k.get("key") for k in (amenity_imgs or []))
    hist_imgs_all = history_amenity_imgs or []
    hist_imgs = [h for h in hist_imgs_all if h.get("key") not in perk_keys]

    has_history = len(hist_imgs) > 0
    history_only_mode = (not has_perks) and has_history

    if has_perks and has_history:
        hist_imgs = hist_imgs[:2]   # keep tight when both present
        show_history = True
    else:
        show_history = history_only_mode

    if show_history:
        history_heading = plan.get("history_heading") or "Amenities from your last stay — now even better"
        history_pitch = plan.get("history_pitch") or (
            "We’ve refreshed and upgraded the facilities you enjoyed previously, ready for you to experience again."
        )
    else:
        history_heading = ""
        history_pitch = ""
        hist_imgs = []

    # Hero copy for header image (kept)
    if has_discount:
        hero_headline = plan.get("hero_headline") or f"{int(discount)}% OFF Your Next Stay"
    elif has_perks:
        hero_headline = plan.get("hero_headline") or f"Enjoy Complimentary {humanize_perks(offer.get('perks'))}"
    else:
        hero_headline = plan.get("hero_headline") or "A Special Offer for Your Next Stay"
    hero_kicker   = plan.get("hero_kicker") or (offer.get("hotel") or "")

    # Big voucher line (badge fallback; HTML computes its own but keep for safety)
    if has_discount:
        big_offer_line = plan.get("big_offer_line") or f"{int(discount)}% OFF • {room_name} • {month} {year}"
    elif has_perks:
        big_offer_line = plan.get("big_offer_line") or f"Enjoy Complimentary {humanize_perks(offer.get('perks'))} • {room_name} • {month} {year}"
    else:
        big_offer_line = plan.get("big_offer_line") or f"{room_name} • {month} {year}"

    # Room caption
    if meal_is_free and meal_name:
        room_caption = plan.get("room_caption") or f"{room_name} • {meal_name} • {month} {year}".strip(" •")
    else:
        room_caption = plan.get("room_caption") or f"{room_name} • {month} {year}".strip(" •")

    template = TEMPLATES["default_html_template"]

    html = template.render(
        plan=plan,
        cta_url=cta_url,
        unsub_url=unsub_url,
        view_url=view_url,

        hero_image_url=hero_img,
        room_image_url=room_img,

        # Complimentary perks only
        amenity_images=amenity_imgs,

        # Previously-used amenities (controlled/trimmed)
        history_amenity_images=hist_imgs,

        hero_headline=hero_headline,
        hero_kicker=hero_kicker,
        big_offer_line=big_offer_line,

        room_caption=room_caption,

        # Complimentary block copy
        amenities_heading=amenities_heading,
        perks_pitch=perks_pitch,

        # History block control + copy
        show_history=show_history,
        history_heading=history_heading,
        history_pitch=history_pitch,

        # variables used by the new badge/subhead helpers in HTML
        discount_pct=discount,
        perks=offer.get("perks") or [],
        room_type_label=room_name,
        target_month=month,
        target_year=year,
        offer_days=offer.get("offer_days"),

        social_links={
            "facebook": offer.get("facebook_url") or "https://facebook.com",
            "instagram": offer.get("instagram_url") or "https://instagram.com",
            "twitter": offer.get("twitter_url") or "https://twitter.com",
        },
        contact_line=plan.get("contact_line"),
        sender=offer.get("hotel", "Our Hotel"),
        sender_address="123 Riverside, London, UK"
    )

    # Plain text mirrors the pitch without claiming perks if there are none
    plain_bits = [
        plan.get("greeting",""),
        "",
        plan.get("opening_line",""),
        plan.get("offer_line",""),
    ]
    if perks_pitch:
        plain_bits.append(perks_pitch)
    plain_bits += ["", f"{plan.get('cta_text','Book Now')}: {cta_url}"]
    plain = "\n".join(plain_bits)

    return {
        **plan,
        "html": html,
        "plain_text": plain,
        "coupon_code": coupon,
    }



def genrate_offer_emails(offer):
    try:
        plan_email = get_email_from_api(offer)
    except Exception as e:
        # log upstream LLM/raw content problems
        print("LLM failure for offer:", offer.get("id"), e)
        # continue with defaults so we don't kill the whole run
        plan_email = {
            "subject": "Your Exclusive Hotel Offer",
            "preheader": "A special rate picked for you",
            "greeting": "Hi {{first_name}},",
            "opening_line": "We’re excited to welcome you back.",
            "offer_line": "Enjoy a limited‑time discount on your next stay.",
            "perks_line": "",
            "cta_text": "Book Now"
        }
    return render_html_with_email(plan_email, offer)


def generate_emails(email, months, year) -> Dict[str, Any]:
    data = get_discount_ofers(email, months, year)
    if not data.get("success"):
        return data  

    discount_offers = data["offers"]
    history_list = data["history"]
    user_id = data["user_id"]

    history_lookup = {h["id"]: h for h in history_list}
    results = []
    for off in discount_offers:
        offer_sanitised = {k: off[k] for k in SAFE_KEYS_OFFER if k in off}

        booking_id = off.get("booking_id")
        if booking_id and booking_id in history_lookup:
            hist = history_lookup[booking_id]
            offer_sanitised["history"] = {k: hist[k] for k in SAFE_KEYS_HISTORY if k in hist}

        try:
            html_email = genrate_offer_emails(offer_sanitised)
        except Exception as e:
            html_email = {
                "subject": "Error",
                "html": "",
                "plain_text": str(e),
                "coupon_code": ""
            }

        first_name = (off.get("name") or "Guest").split()[0]

        subject_with_name = name_in(html_email.get("subject", ""), first_name)
        preheader_with_name = name_in(html_email.get("preheader", ""), first_name)
        html_with_name = name_in(html_email.get("html", ""), first_name)
        plain_with_name = name_in(html_email.get("plain_text", ""), first_name)
        results.append({
            "customer": off.get("name"),  
            "offer_id": off.get("id"),
            "email": {
                **html_email,
                "subject": subject_with_name,
                "preheader": preheader_with_name,
                "html": html_with_name,
                "plain_text": plain_with_name,
            }
        })

    save_res = save_email_campaigns(user_id=user_id, emails=results)
    response = fetch_campaign_stats(email)
    return response




def fetch_campaign_stats(user_email: str):
    """
    Return stats + minimal campaign card data:
    {
      years → months → { total, generated, pending },
      campaigns → { year → month → [cards] },
      month_labels
    }
    """

    user_res = supabase.table("users").select("user_id").eq("email", user_email).execute()
    if not user_res.data:
        return {"years": {}, "campaigns": {}, "month_labels": {}}
    user_id = user_res.data[0]["user_id"]

    res = supabase.from_("discount_offers").select(
        """
        id, target_year, target_month, hotel, business_label, discount_pct,
        email_campaigns!left (id, subject, preheader, status, created_at)
        """
    ).eq("user_id", user_id).eq("is_active", True).execute()

    offers = res.data or []

    stats = {}
    campaigns_by_month = {}

    for o in offers:
        year = o.get("target_year")
        month = o.get("target_month")
        if not year or not month:
            continue

        if isinstance(month, str):
            month = MONTH_NAME_TO_NUM.get(month.lower())
        if not isinstance(month, int) or not (1 <= month <= 12):
            continue

        stats.setdefault(year, {m: {"total": 0, "generated": 0, "pending": 0} for m in range(1, 13)})
        campaigns_by_month.setdefault(year, {m: [] for m in range(1, 13)})

        stats[year][month]["total"] += 1

        ec_list = o.get("email_campaigns") or []
        ec = ec_list[0] if ec_list else None
        if ec:
            stats[year][month]["generated"] += 1
        else:
            stats[year][month]["pending"] += 1

        campaigns_by_month[year][month].append({
            "offer_id": o["id"],
            "campaign_id": ec.get("id") if ec else None,
            "hotel": o.get("hotel"),
            "business_label": o.get("business_label"),
            "discount_pct": o.get("discount_pct"),
            "status": ec.get("status") if ec else "pending",
            "subject": ec.get("subject") if ec else None,
            "preheader": ec.get("preheader") if ec else None,
            "created_at": ec.get("created_at") if ec else None,
        })

    return {
        "years": stats,
        "campaigns": campaigns_by_month,
        "month_labels": {i: MONTH_NAMES[i - 1] for i in range(1, 13)},
    }

    
def save_email_campaigns(user_id: str, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Save generated emails into email_campaigns table.
    `emails` is a list of dicts with {offer_id, email: {...}}
    """
    try:
        rows = []
        for e in emails:
            offer_id = e.get("offer_id")
            email = e.get("email", {})

            row = {
                "id": str(uuid.uuid4()),
                "offer_id": offer_id,
                "user_id": user_id,
                "subject": email.get("subject"),
                "preheader": email.get("preheader"),
                "greeting": email.get("greeting"),
                "opening_line": email.get("opening_line"),
                "offer_line": email.get("offer_line"),
                "perks_line": email.get("perks_line"),
                "perks_pitch": email.get("perks_pitch"),
                "cta_text": email.get("cta_text"),
                "html": email.get("html"),
                "plain_text": email.get("plain_text"),
                "status": "generated",
            }
            rows.append(row)

        if not rows:
            return {"success": False, "message": "No rows to insert"}

        resp = supabase.table("email_campaigns").insert(rows).execute()

        if resp.error:
            return {"success": False, "message": f"DB insert error: {resp.error}"}

        return {"success": True, "inserted": len(rows)}

    except Exception as e:
        return {"success": False, "message": f"Error saving campaigns: {str(e)}"}
      
      
def fetch_email_preview(campaign_id: str):
    try:
        response = (
            supabase.table("email_campaigns")
            .select("html")
            .eq("id", campaign_id)
            .execute()
        )
        if not response.data:
            return {"success": False, "message": "No campaign found"}
        return {"success": True, "html": response.data[0]["html"]}
    except Exception as e:
        return {"success": False, "message": str(e)}


def hotel_kind(hotel: str) -> str:
    h = (hotel or "").lower()
    if "resort" in h:
        return "resort"
    if "city" in h:
        return "city"
    # default
    return "city"

def room_letter(value: str) -> str:
    return (value or "").strip().upper()

def letter_to_tier(letter: str, kind: str) -> str:
    mapping = ROOM_LETTER_TIER.get(kind)
    if not mapping:
        mapping = ROOM_LETTER_TIER["resort"] 
    return mapping.get(letter, "Standard Room")
  
def friendly_room_name(letter: str, hotel: str) -> str:
    
    kind = hotel_kind(hotel)
    tier = letter_to_tier(room_letter(letter), kind)
    return ROOM_TIER_FRIENDLY.get(tier, tier.title())

def map_amenity_name(name: str) -> str | None:
    if not name:
        return None
    n = name.lower()
    if "gym" in n:
        return "gym"
    if "pool" in n or "swim" in n:
        return "swimming_pool"
    if "spa" in n:
        return "spa"
    if "kid" in n:
        return "kids_play_area"
    if "meeting" in n or "conference" in n:
        return "meeting_room"
    if "meal" in n or "breakfast" in n or "dining" in n:
        return "meal"
    return None

def select_images_for_offer(offer: Dict[str, Any]) -> Dict[str, Any]:
    kind = hotel_kind(offer.get("hotel"))
    assets = ASSETS.get(kind, ASSETS["city"])

    letter = room_letter(offer.get("room_type"))
    tier = letter_to_tier(letter, kind)

    room_img = assets["rooms"].get(tier) or next(iter(assets["rooms"].values()))
    hero_img = assets.get("hero") or room_img

    # -------- Complimentary perks (use perk-context mapper) --------
    perk_keys: List[str] = []
    for p in (offer.get("perks") or []):
        k = map_amenity_name(p, context="perk")  # <- returns e.g. "bar_credit"
        if k and (k in assets["amenities"]) and (k not in perk_keys):
            perk_keys.append(k)
    perk_keys = perk_keys[:3]  # cap visuals

    # Build the set of perk families for de-duping (e.g., {"bar", "pool"})
    perk_families = {amenity_family(k) for k in perk_keys}

    # -------- Previously-used amenities (use history-context mapper) --------
    used_before_keys: List[str] = []
    for p in (offer.get("amenities_used_before") or []):
        hk = map_amenity_name(p, context="history")  # <- returns e.g. "bar"
        if not hk or hk not in assets["amenities"]:
            continue
        # De-dupe: skip if its family is already covered by any free perk
        if amenity_family(hk) in perk_families:
            continue
        if hk not in used_before_keys:
            used_before_keys.append(hk)
    used_before_keys = used_before_keys[:3]

    def _mk_items(keys: List[str]):
        return [
            {
                "key": k,
                "url": assets["amenities"][k],
                "label": AMENITY_LABELS.get(k, k.replace("_", " ").title()),
                "subtitle": AMENITY_SLOGANS.get(k, "Complimentary for your stay"),
            }
            for k in keys
        ]

    return {
        "hero_image_url": hero_img,
        "room_image_url": room_img,
        "amenity_images": _mk_items(perk_keys),               # FREE perks (e.g., Bar Credit)
        "history_amenity_images": _mk_items(used_before_keys),# Facilities used (e.g., Bar)
        "room_tier": tier,
        "amenity_keys": perk_keys,
    }


    

def month_nums_to_names(months: list[int]) -> list[str]:
    """Convert [1,2,3] → ['January','February','March']; ignores invalid entries."""
    names = []
    for m in months or []:
        if isinstance(m, int) and 1 <= m <= 12:
            names.append(MONTH_NAMES[m - 1])
    return names
  
def extract_json(text: str) -> str:
        """Extract first {...} JSON block from text, stripping markdown fences."""
        # remove markdown fences like ```json ... ```
        cleaned = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", text.strip(), flags=re.M)
        # extract JSON object only
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if match:
            return match.group(0)
        return cleaned  # fallback
      
      
def build_history_context(history: Dict[str, Any]) -> str:
    if not history:
        return "No prior booking context available."

    amenities_used = [
        label for label, used in {
            "Spa": history.get("is_spa_used"),
            "Gym": history.get("is_gym_used"),
            "Swimming Pool": history.get("is_swimming_pool_used"),
            "Bar": history.get("is_bar_used"),
            "Kids Club": history.get("is_kids_club_used"),
            "Meeting Room": history.get("is_meeting_room_used"),
        }.items() if used
    ]
    amenities_str = ", ".join(amenities_used) if amenities_used else "none"

    return f"""
    Last stay: {history.get('arrival_date_month')} {history.get('arrival_date_year')}, 
    {history.get('total_stay_length')} nights, {history.get('adults')} adults, {history.get('children')} children.
    Room: {friendly_room_name(history.get('reserved_room_type'), history.get('hotel'))}.
    Amenities used: {amenities_str}.
    Customer type: {history.get('customer_type')}.
    High spender: {"yes" if history.get("is_high_spender") else "no"}.
    """
    
def name_in(s: str,first_name) -> str:
    return (s or "").replace("{{first_name}}", first_name).replace("{first_name}", first_name)

     
def humanize_perks(perk_slugs):
    # turn ["kids_club","bar_credit","gym"] into "Kids Club, Bar Credit and Gym"
    words = [map_amenity_name(p).replace("_"," ").title() for p in (perk_slugs or [])]
    if not words: return ""
    if len(words) == 1: return words[0]
    if len(words) == 2: return f"{words[0]} and {words[1]}"
    return f"{', '.join(words[:-1])}, and {words[-1]}"

def plural_nights(n):
    try:
        n = int(n)
        return f"{n} night" if n == 1 else f"{n} nights"
    except Exception:
        return ""

def map_amenity_name(name: str, *, context: str = "perk") -> str | None:
    """
    Map free-perk names and history/facility names to asset keys.
    context: "perk" (default), "history"
    """
    if not name:
        return None
    n = name.lower()

    if "gym" in n:
        return "gym"
    if "pool" in n or "swim" in n:
        return "swimming_pool"
    if "spa" in n:
        return "spa"
    if "kid" in n or "club" in n:
        return "kids_club"
    if "meeting" in n or "conference" in n:
        return "meeting_room"
    if "meal" in n or "breakfast" in n or "dining" in n:
        return "meal"
    if "desk" in n:
        return "work_desk"
    if "bar" in n:
        # Perks should show "Bar Credit", history should show "Bar"
        return "bar_credit" if context == "perk" else "bar"

    return None


def amenity_family(key: str) -> str:
    """Canonical bucket for de-duping across perk vs facility names."""
    k = (key or "").lower()
    if k in {"bar_credit", "bar"}: return "bar"
    if k in {"kids_club", "kids_play_area"}: return "kids"
    if k in {"swimming_pool"}: return "pool"
    if k in {"gym"}: return "gym"
    if k in {"spa"}: return "spa"
    if k in {"meeting_room"}: return "meeting_room"
    if k in {"work_desk"}: return "work_desk"
    if k in {"meal"}: return "meal"
    return k  # fallback: treat as its own family
