const apiUrl = import.meta.env.VITE_API_ENDPOINT  

const apiUtils = () => {
  const uploadBookingFile = async (file:File) => {
    const response = await fetch(`${apiUrl}/data-cleanup/uploadbookingfile`, {
      method: 'POST',
      body: file,
    })
    const data = await response.json()
    console.log(data)
  }

  return { uploadBookingFile }
}

export default apiUtils
