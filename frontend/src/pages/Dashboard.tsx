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
    const [segmentProfile, setSegmentProfile] = usePersistentState("segmentProfile", [])
    const [creatingSegment, setCreatingSegment] = useState(false)
    const [bookingRecordCount, setBookingRecordCount] = usePersistentState("booking_record", 0)
    const [segmentCounts, setSegmentCounts] = usePersistentState<Record<number, number>>("segmentCounts", {});


    const [files, setFiles] = usePersistentState<{
        bookingFile: string | null
        financeFile: string | null
    }>('files', {
        bookingFile: null,
        financeFile: null
    });
    const [isProcessing, setIsProcessing] = useState<boolean>(false)
    const [step, setStep] = useState<number>(1);

    const { uploadBookingFile, genrateCustomerSegments, getSegmentProfiles } = apiUtils();

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
        setIsProcessing(true)
        const response = await uploadBookingFile(file, email);
        if (response.success) {
            setIsProcessing(false)
            setMessage("Booking file Uploaded succesfully.")
        }
        else {
            setError("Error while uploading the file.")
        }
        console.log(response)
    }

    const financeFileUpload = async (file: File) => {
        setIsProcessing(true)
        const response = await uploadBookingFile(file, email);
        setIsProcessing(false)
        console.log(response)
    }
    const getSegmentProfile = async () => {
        const response = await getSegmentProfiles(email)
        setSegmentProfile(response.data)
        console.log(response)
    }

    const genrateSegments = async () => {
        setIsProcessing(true);
        setCreatingSegment(true);
        const response = await genrateCustomerSegments(email);
        if (response.success) {
            setSegmentCounts(response.segment_counts); // store counts from backend
        }
        setIsProcessing(false);
        setCreatingSegment(false);
    };


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
                    <FileUpload lable="Step 1: Upload your booking history file." file={files.bookingFile} isUploading={isProcessing} handleUpload={handleFileUpload} handleRemove={handleRemove} />
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
                    <FileUpload lable="Step 2: Upload your finance file." file={files.financeFile} isUploading={isProcessing} handleUpload={handleFileUpload} handleRemove={handleRemove} />
                    <div className="mt-5">
                        <p className="text-green-400 ">{message}</p>
                        <p className="text-red-400">{error}</p>
                    </div>
                    <div className="w-full flex flex-row mt-5 justify-around px-4">
                        <Button disabled={false} type='normal' label='Back' onClick={() => setStep(step - 1)} />
                        <Button disabled={!files.financeFile} type='normal' label='Next' onClick={() => { setStep(step + 1); setMessage(""); getSegmentProfile() }} />
                    </div>
                </div>
            }

            {step === 3 && (
                <div className="w-full px-4 flex flex-col items-center pt-2 text-center">
                    <h1 className="text-2xl font-semibold text-gray-800 mb-1">
                        Step 3: Generate customer segments
                    </h1>
                    <p className="text-gray-600 mb-6 text-sm">
                        Our model will categorise your customers into these segments:
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6 w-full max-w-5xl">
                        {segmentProfile?.map((profile: any) => {
                            const iconMap: Record<number, string> = {
                                0: "👥",
                                1: "👨‍👩‍👧",
                                2: "💻",
                                3: "💼",
                                4: "⭐",
                            };

                            return (
                                <div
                                    key={profile.cluster_id}
                                    className="p-4 bg-white border border-gray-100 rounded-lg shadow-sm hover:shadow-md transition-shadow"
                                >
                                    {/* Title Row */}
                                    <div className="flex justify-between items-center mb-3">
                                        <div className="flex items-center gap-2">
                                            <span className="text-lg">{iconMap[profile.cluster_id]}</span>
                                            <h3 className="text-sm font-semibold text-gray-800">
                                                {profile.business_label}
                                            </h3>
                                        </div>
                                        {(Object.keys(segmentCounts)).length > 0 &&
                                            <span className="bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded-full animate-pulse">
                                                {segmentCounts?.[profile.cluster_id] || 0} records
                                            </span>
                                        }
                                    </div>

                                    {/* Tags */}
                                    <div className="flex flex-wrap gap-1">
                                        {profile.tags.map((tag: string) => (
                                            <span
                                                key={tag}
                                                className="bg-blue-50 text-blue-700 text-[10px] px-2 py-0.5 rounded-full border border-blue-100 hover:bg-blue-100 transition-colors"
                                            >
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    {creatingSegment && (
                        <div className="mt-4">
                            <p className="text-gray-800 font-medium animate-pulse">
                                Please wait while we create your personalised customer segments.
                                <br />
                                This might take a couple of minutes...
                            </p>
                            <div className="flex justify-center mt-6">
                                <div className="h-8 w-8 border-4 border-blue-500 border-dashed rounded-full animate-spin"></div>
                            </div>
                            {error && <p className="text-red-500 mt-4">{error}</p>}
                        </div>
                    )}

                    {/* Buttons */}
                    <div className="w-full flex flex-row justify-between px-4 mt-6 max-w-md">
                        <Button
                            type="normal"
                            disabled={isProcessing}
                            label="Back"
                            onClick={() => setStep(step - 1)}
                        />
                        {(Object.keys(segmentCounts)).length == 0 &&
                            <Button
                                type="normal"
                                disabled={isProcessing}
                                label="Generate Segments"
                                onClick={() => genrateSegments()}
                            />
                        }
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
