const apiUrl = import.meta.env.VITE_API_ENDPOINT

const apiUtils = () => {
  const uploadBookingFile = async (file: File, email: string) => {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("email", email)
    const response = await fetch(`${apiUrl}/process-bookings/uploadbookingfile`, {
      method: 'POST',
      body: formData,
    })
    const data = await response.json()
    return data
  }

  const uploadFinanacialsFile = async (file: File, email: string) => {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("email", email)
    const response = await fetch(`${apiUrl}/financials/uploadfinancials`, {
      method: 'POST',
      body: formData,
    })
    const data = await response.json()
    return data
  }

  const generateDiscountsAPI = async (email: string, config: any) => {
    const res = await fetch(`${apiUrl}/discounts/genrate_discounts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, config }),
    });
    const data = await res.json().catch(() => ({}));
    return { success: res.ok, ...data };
  };

  // 📌 New: Fetch discount summary
  const getDiscountSummary = async (email: string) => {
    const res = await fetch(`${apiUrl}/discounts/summary?email=${encodeURIComponent(email)}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    })
    return await res.json()
  }



  const validateUser = async (email: string) => {
    const formData = new FormData()
    formData.append("email", email)
    const response = await fetch(`${apiUrl}/auth/validateuser`, {
      method: "POST",
      body: formData
    })

    const result = await response.json()
    return result

  }

  const genrateCustomerSegments = async (email: string) => {
    const formData = new FormData()
    formData.append("email", email)
    const response = await fetch(`${apiUrl}/segment/genrate-segments`, {
      method: "POST",
      body: formData
    })

    const result = await response.json()
    return result
  }

  const getSegmentProfiles = async (email: string) => {
    const formData = new FormData()
    formData.append("email", email)
    const response = await fetch(`${apiUrl}/segment/get-segment-profiles`,
      {
        method: "POST",
        body: formData
      }
    )
    const result = await response.json()

    return result

  }
  const generateEmailsAPI = async (email:string,months:any, year:number)=>{
    const body = { email, year, months };
    const response = await fetch(`${apiUrl}/email/generate-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const err = await response.text();
      console.error("Generate failed:", err);
    }
    const result = await response.json()
    return result
  }

  const getEmailCampaign = async (email:string)=>{
    const formData = new FormData()
    formData.append("email", email)
    const response = await fetch(`${apiUrl}/email/get-email-campaigns`,
      {
        method: "POST",
        body: formData
      }
    )
    const result = await response.json()

    return result
  }

  const getEmailPreview = async (id:string)=>{
    const body = { campaign_id: id };
    const response = await fetch(`${apiUrl}/email/get-email-preview`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }
    )
    const result = await response.json()

    return result
  }

  const launchEmailCampaign = async (payload: {
    user_email: string;
    campaign: { name: string; description?: string | null };
    scope: { year: number; months: number[] };
    email_campaign_ids: string[];
    schedule: { mode: "now" | "later" | "smart"; schedule_at: string | null; timezone: string };
    compliance: Record<string, boolean>;
  }) => {
    const res = await fetch(`${apiUrl}/campaign/launch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return await res.json(); // -> { success, marketing_campaign_id, batch_id, queued_count }
  };

  return { uploadBookingFile, 
    validateUser, 
    genrateCustomerSegments, 
    getSegmentProfiles,
     uploadFinanacialsFile, 
     generateDiscountsAPI, 
     getDiscountSummary,
     generateEmailsAPI,
     getEmailCampaign,getEmailPreview,
     launchEmailCampaign
      }
}




export default apiUtils
