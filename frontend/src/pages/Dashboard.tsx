import FileUpload from "../components/dashboard/FileUpload";

import React, { useEffect, useState } from "react";
import apiUtils from "..//utils/apiUtils";
import Button from "../components/shared/Button";
import { usePersistentState } from "../hooks/usePersistanceStorage";
import Stepper from "../components/dashboard/Stepper";

export default function Dashboard() {
    const [email] = usePersistentState<string>('email', '')
    const [message, setMessage] = useState("")
    const [error, setError] = useState("")

    const [files, setFiles] = usePersistentState<{
        bookingFile: string | null
        financeFile: string | null
    }>('files', {
        bookingFile: null,
        financeFile: null
    });
    const [isUploading, setIsUploding] = useState<boolean>(false)
    const [step, setStep] = useState<number>(1);

    const { uploadBookingFile } = apiUtils();

    useEffect(() => {
        setTimeout(() => {
            setError("")
            setMessage("")
        }, 1000);

    }, [message, error])

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) {
            console.error("No file selected");
            return;
        }
        if (file && step === 1) {
            setFiles((prev) => ({ ...prev, bookingFile: file.name }))
            bookingFileUpload(file)
            console.log("Uploaded file:", file);
        }
        if (file && step === 2) {
            setFiles((prev) => ({ ...prev, financeFile: file.name }))
            financeFileUpload(file)
            console.log("Uploaded file:", file);
        }
    };

    const bookingFileUpload = async (file: File) => {
        setIsUploding(true)
        const response = await uploadBookingFile(file, email);
        if (response.success) {
            setIsUploding(false)
            setMessage("Booking file Uploaded succesfully.")
        }
        else {
            setError("Error while uploading the file.")
        }
        console.log(response)
    }

    const financeFileUpload = async (file: File) => {
        setIsUploding(true)
        const response = await uploadBookingFile(file, email);
        setIsUploding(false)
        console.log(response)

    }
    const handleRemove = () => {

        if (step == 1) {
            //api call
            setFiles((prev) => ({ ...prev, bookingFile: "" }))
        }
        if (step == 2) {
            //api call
            setFiles((prev) => ({ ...prev, financeFile: "" }))
        }
    }
    return (
        <>
            <Stepper step={step} />
            {step == 1 &&
                <div className='flex flex-col items-center pt-16'>
                    <FileUpload lable="Step 1: Upload your booking history file." file={files.bookingFile} isUploading={isUploading} handleUpload={handleFileUpload} handleRemove={handleRemove} />
                    <div className="mt-5">
                        <p className="text-green-400">{message}</p>
                        <p className="text-red-400">{error}</p>
                    </div>
                    <div className="mt-5">
                        <Button disabled={!files.bookingFile} type='normal' label='Next' onClick={() => { setStep(step + 1); setMessage("") }} />
                    </div>
                </div>
            }
            {step == 2 &&
                <div className='flex flex-col items-center pt-16'>
                    <FileUpload lable="Step 2: Upload your finance file." file={files.financeFile} isUploading={isUploading} handleUpload={handleFileUpload} handleRemove={handleRemove} />
                    <div className="mt-5">
                        <p className="text-green-400 ">{message}</p>
                        <p className="text-red-400">{error}</p>
                    </div>
                    <div className="w-full flex flex-row mt-5 justify-around px-4">
                        <Button disabled={false} type='normal' label='Back' onClick={() => setStep(step - 1)} />
                        <Button disabled={!files.financeFile} type='normal' label='Next' onClick={() => { setStep(step + 1); setMessage("") }} />
                    </div>
                </div>
            }

            {step === 3 && (
                <div className="w-full px-4 flex flex-col items-center pt-16 text-center">
                    <h1 className="text-2xl font-semibold text-gray-800 mb-4">
                        Step 3: Generate customer segments
                    </h1>

                    <div className="mt-4 mb-6">
                        <p className="text-gray-800 font-medium animate-pulse">
                            Please wait while we create your personalised customer segments.<br />
                            This might take a couple of minutes...
                        </p>

                        {/* Optional: Add loader */}
                        <div className="flex justify-center mt-6">
                            <div className="h-8 w-8 border-4 border-blue-500 border-dashed rounded-full animate-spin"></div>
                        </div>

                        {/* Error Display */}
                        {error && <p className="text-red-500 mt-4">{error}</p>}
                    </div>

                    <div className="w-full flex flex-row justify-around px-4 mt-6">
                        <Button type="normal" disabled={isUploading} label="Back" onClick={() => setStep(step - 1)} />
                        <Button
                            type="normal"
                            label="Next"
                            disabled={!files.financeFile}
                            onClick={() => setStep(step + 1)}
                        />
                    </div>
                </div>
            )}


        </>
    )
}
