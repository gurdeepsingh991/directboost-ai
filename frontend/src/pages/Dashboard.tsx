import FileUpload from "../components/dashboard/FileUpload";

import React, { useEffect, useState } from "react";
import apiUtils from "..//utils/apiUtils";
import Button from "../components/shared/Button";
import { usePersistentState } from "../hooks/usePersistanceStorage";
import Stepper from "../components/dashboard/Stepper";

export default function Dashboard() {

    const [files, setFiles] = usePersistentState<{
        bookingFile: string | null
        financeFile: string | null
    }>('files',{
        bookingFile: null,
        financeFile: null
    });
    const [isUploading, setIsUploding] = useState<boolean>(false)
    const [step, setStep] = useState<number>(1);

    const { uploadBookingFile } = apiUtils();

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
        const response = await uploadBookingFile(file);
        setIsUploding(false)
        console.log(response)
    }

    const financeFileUpload = async (file: File) => {
        setIsUploding(true)
        const response = await uploadBookingFile(file);
        setIsUploding(false)
        console.log(response)

    }
    const handleRemove = () => {

        if(step==1){
            //api call
            setFiles ((prev)=> ({...prev,bookingFile:""}))
        }
        if(step==2){
            //api call
            setFiles ((prev)=> ({...prev,financeFile:""}))
        }
    }
    return (
        <>
             <Stepper step={step} />
            {step == 1 &&
                <div className='flex flex-col items-center pt-16'>
                    <FileUpload lable="Step 1: Upload your booking history file." file={files.bookingFile} isUploading={isUploading} handleUpload={handleFileUpload} handleRemove={handleRemove} />
                    <div className="mt-5">
                        <Button disabled={!files.bookingFile} type='normal' label='Next' onClick={() => setStep(step + 1)} />
                    </div>
                </div>
            }
            {step == 2 &&
                <div className='flex flex-col items-center pt-16'>
                    <FileUpload lable="Step 2: Upload your finance file." file={files.financeFile} isUploading={isUploading} handleUpload={handleFileUpload} handleRemove={handleRemove} />
                    <div className="w-full flex flex-row mt-5 justify-around px-4">
                        <Button disabled={false} type='normal' label='Back' onClick={() => setStep(step - 1)} />
                        <Button disabled={!files.financeFile} type='normal' label='Next' onClick={() => setStep(step + 1)} />
                    </div>
                </div>
            }

        </>
    )
}
