const apiUrl = import.meta.env.VITE_API_ENDPOINT  

const apiUtils = () => {
  const uploadBookingFile = async (file:File) => {
    const formData = new FormData()
    formData.append("file",file)
    const response = await fetch(`${apiUrl}/data-cleanup/uploadbookingfile`, {
      method: 'POST',
      body: formData,
    })
    const data = await response.json()
    return data
  }

  return { uploadBookingFile }
}

export default apiUtils
