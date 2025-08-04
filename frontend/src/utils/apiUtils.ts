const apiUrl = import.meta.env.VITE_API_ENDPOINT

const apiUtils = () => {
  const uploadBookingFile = async (file: File,email:string) => {
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

  const genrateCustomerSegments = async (email:string)=>{
      const formData = new FormData()
      formData.append("email", email)
      const response = await fetch(`${apiUrl}/segment/genrate-segments`, {
        method: "POST",
        body: formData
      })
  
      const result = await response.json()
      return result
  }

  return { uploadBookingFile, validateUser,genrateCustomerSegments }
}




export default apiUtils
