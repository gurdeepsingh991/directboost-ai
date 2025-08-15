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

  const generateDiscounts = async (email: string, config: any) => {
    const res = await fetch(`${apiUrl}/discounts/genrate_discounts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, config }),
    });
    const data = await res.json().catch(() => ({}));
    return { success: res.ok, ...data };
  };


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

  return { uploadBookingFile, validateUser, genrateCustomerSegments, getSegmentProfiles, uploadFinanacialsFile, generateDiscounts }
}




export default apiUtils
