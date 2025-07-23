import React, { useEffect } from "react";
import apiUtils from "../../utils/apiUtils";

export default function FileUpload() {
    const { uploadBookingFile } = apiUtils();

    
    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            console.log("Uploaded file:", file);
        }
        if (!file) {
            console.error("No file selected");
            return;
          }

       const response = await uploadBookingFile(file);
        console.log(response)

    };
    return (
        <div className="flex items-center flex-col justify-center w-full mt-10">

            <h1 className="text-3xl">Upload your csv file to start the process</h1>

            <label className="flex flex-col items-center justify-center w-full mt-9 max-w-md h-64 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <svg
                        className="w-8 h-8 mb-4 text-gray-500"
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
                    <p className="mb-2 text-sm text-gray-500">
                        <span className="font-semibold">Click to upload</span> or drag and drop
                    </p>
                    <p className="text-xs text-gray-500">CSV or XLSX files only</p>
                </div>
                <input
                    type="file"
                    accept=".csv,.xlsx"
                    className="hidden"
                    onChange={handleFileUpload}
                />
            </label>
        </div>
    );
}
