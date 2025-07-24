
interface FileUploadProps {
    lable: string
    file: string|null
    handleUpload: (e: React.ChangeEvent<HTMLInputElement>) => void
    handleRemove: () => void
    isUploading: boolean
}

export default function FileUpload({ lable, handleUpload, handleRemove, file, isUploading }: FileUploadProps) {
   
    return (
        <div className="flex flex-col items-center w-full mt-10 px-4 text-center">
        <h1 className="text-2xl font-semibold text-gray-800 mb-4">{lable}</h1>
      
        {/* File Upload Drop Area */}
        {!file && (
          <label className="flex flex-col items-center justify-center w-full max-w-md h-64 border-2 border-dashed border-gray-300 rounded-xl cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors">
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <svg
                className="w-8 h-8 mb-3 text-gray-500"
                aria-hidden="true"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 20 16"
              >
                <path
                  stroke="currentColor"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 13h3a3 3 0 0 0 0-6h-.025
                    A5.56 5.56 0 0 0 16 6.5
                    5.5 5.5 0 0 0 5.207 5.021
                    C5.137 5.017 5.071 5 5 5
                    a4 4 0 0 0 0 8h2.167
                    M10 15V6m0 0L8 8m2-2 2 2"
                />
              </svg>
              <p className="text-sm text-gray-500 mb-1">
                <span className="font-medium text-gray-700">Click to upload</span> or drag and drop
              </p>
              <p className="text-xs text-gray-400">CSV or XLSX files only</p>
            </div>
            <input
              type="file"
              accept=".csv,.xlsx"
              className="hidden"
              onChange={handleUpload}
            />
          </label>
        )}
      
        {/* Uploading Indicator */}
        {isUploading && (
          <p className="mt-4 text-sm text-blue-600 animate-pulse">Uploading...</p>
        )}
      
        {/* Uploaded File Preview */}
        {file && (
          <div className="flex items-center justify-between mt-5 w-full max-w-md bg-blue-50 border border-blue-200 rounded-xl px-4 py-2">
            <p className="text-sm font-medium text-blue-800 truncate max-w-[70%]">
              {file}
            </p>
            <button
              onClick={handleRemove}
              className="text-red-500 cursor-pointer hover:underline text-sm"
            >
              Remove
            </button>
          </div>
        )}
      </div>
      
    );
}
