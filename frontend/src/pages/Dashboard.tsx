import FileUpload from "../components/dashboard/FileUpload";
import React, { useEffect, useState } from "react";
import apiUtils from "../utils/apiUtils";
import Button from "../components/shared/Button";
import { usePersistentState } from "../hooks/usePersistanceStorage";
import Stepper from "../components/dashboard/Stepper";
import Discounts from "../components/dashboard/Discounts";

export default function Dashboard() {
    const [email] = usePersistentState<string>("email", "");
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [segmentProfile, setSegmentProfile] = usePersistentState("segmentProfile", []);
    const [creatingSegment, setCreatingSegment] = useState(false);
    // const [bookingRecordCount, setBookingRecordCount] = usePersistentState("booking_record", 0);
    const [segmentCounts, setSegmentCounts] =
        usePersistentState<Record<number, number>>("segmentCounts", {});
    const [files, setFiles] = usePersistentState<{ bookingFile: string | null; financeFile: string | null }>(
        "files",
        { bookingFile: null, financeFile: null }
    );
    const [isProcessing, setIsProcessing] = useState<boolean>(false);
    const [step, setStep] = usePersistentState<number>("step", 1);

    const { uploadBookingFile, genrateCustomerSegments, getSegmentProfiles, uploadFinanacialsFile } =
        apiUtils();

    useEffect(() => {
        const t = setTimeout(() => {
            setError("");
            setMessage("");
        }, 1000);
        return () => clearTimeout(t);
    }, [message, error]);

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (step === 1) {
            setFiles((prev) => ({ ...prev, bookingFile: file.name }));
            bookingFileUpload(file);
        } else if (step === 2) {
            setFiles((prev) => ({ ...prev, financeFile: file.name }));
            financeFileUpload(file);
        }
    };

    const bookingFileUpload = async (file: File) => {
        setIsProcessing(true);
        const response = await uploadBookingFile(file, email);
        setIsProcessing(false);
        if (response.success) setMessage("Booking file uploaded successfully.");
        else setError("Error while uploading the file.");
    };

    const financeFileUpload = async (file: File) => {
        setIsProcessing(true);
        await uploadFinanacialsFile(file, email);
        setIsProcessing(false);
    };

    const getSegmentProfile = async () => {
        const response = await getSegmentProfiles(email);
        setSegmentProfile(response.data);
    };

    const genrateSegments = async () => {
        setIsProcessing(true);
        setCreatingSegment(true);
        const response = await genrateCustomerSegments(email);
        if (response.success) setSegmentCounts(response.segment_counts);
        setIsProcessing(false);
        setCreatingSegment(false);
    };

    const handleRemove = () => {
        if (step === 1) setFiles((prev) => ({ ...prev, bookingFile: "" }));
        if (step === 2) setFiles((prev) => ({ ...prev, financeFile: "" }));
    };

    /** Fixed action bar (viewport-fixed) */
    const FixedActionBar = ({ children }: { children: React.ReactNode }) => (
        <>
            {/* spacer to avoid overlap */}
            <div className="h-24" />
            <div
                className="
          fixed inset-x-0 bottom-0 z-40
          border-t border-gray-200
          bg-white/90 backdrop-blur supports-[backdrop-filter]:bg-white/70
          shadow-[0_-6px_12px_-8px_rgba(0,0,0,0.15)]
          py-3
          pb-[calc(0.75rem+env(safe-area-inset-bottom))]
        "
            >
                <div className="max-w-6xl mx-auto px-4">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                        <div className="flex flex-col">
                            <span className="text-sm font-medium text-gray-800">
                                {step === 1 && "Step 1: Upload Booking"}
                                {step === 2 && "Step 2: Upload Finance"}
                                {step === 3 && "Step 3: Segmentation"}
                            </span>
                            <span className="text-xs text-gray-500">
                                Your progress is saved locally. Continue when ready.
                            </span>
                        </div>
                        <div className="flex items-center gap-2 sm:gap-3">{children}</div>
                    </div>
                </div>
            </div>
        </>
    );

    return (
        <>
            <Stepper step={step} />

            {/* STEP 1 */}
            {step === 1 && (
                <div className="flex flex-col items-center pt-40 px-4">
                    <FileUpload
                        lable="Upload your booking history file."
                        file={files.bookingFile}
                        isUploading={isProcessing}
                        handleUpload={handleFileUpload}
                        handleRemove={handleRemove}
                    />
                    <div className="mt-5">
                        <p className="text-green-400">{message}</p>
                        <p className="text-red-400">{error}</p>
                    </div>

                    <FixedActionBar>
                        <span className="hidden sm:block" />
                        <Button
                            disabled={!files.bookingFile}
                            type="normal"
                            label="Next"
                            onClick={() => {
                                setStep(step + 1);
                                setMessage("");
                            }}
                        />
                    </FixedActionBar>
                </div>
            )}

            {/* STEP 2 */}
            {step === 2 && (
                <div className="flex flex-col items-center pt-40 px-4">
                    <FileUpload
                        lable="Upload your finance file."
                        file={files.financeFile}
                        isUploading={isProcessing}
                        handleUpload={handleFileUpload}
                        handleRemove={handleRemove}
                    />
                    <div className="mt-5">
                        <p className="text-green-400">{message}</p>
                        <p className="text-red-400">{error}</p>
                    </div>

                    <FixedActionBar>
                        <Button type="normal" label="Back" onClick={() => setStep(step - 1)} />
                        <Button
                            disabled={!files.financeFile}
                            type="normal"
                            label="Next"
                            onClick={() => {
                                setStep(step + 1);
                                setMessage("");
                                getSegmentProfile();
                            }}
                        />
                    </FixedActionBar>
                </div>
            )}

            {/* STEP 3 */}
            {step === 3 && (
                <div className="w-full px-4 flex flex-col items-center pt-40 text-center">
                    <h1 className="text-2xl font-semibold text-gray-800 mb-1">
                       Generate customer segments
                    </h1>
                    <p className="text-gray-600 mb-6 text-sm">Our model will categorise your customers into these segments:</p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6 w-full max-w-5xl">
                        {segmentProfile?.map((profile: any) => {
                            const iconMap: Record<number, string> = { 0: "👥", 1: "👨‍👩‍👧", 2: "💻", 3: "💼", 4: "⭐" };
                            return (
                                <div
                                    key={profile.cluster_id}
                                    className="p-4 bg-white border border-gray-100 rounded-lg shadow-sm hover:shadow-md transition-shadow"
                                >
                                    <div className="flex justify-between items-center mb-3">
                                        <div className="flex items-center gap-2">
                                            <span className="text-lg">{iconMap[profile.cluster_id]}</span>
                                            <h3 className="text-sm font-semibold text-gray-800">{profile.business_label}</h3>
                                        </div>
                                        {Object.keys(segmentCounts).length > 0 && (
                                            <span className="bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded-full animate-pulse">
                                                {segmentCounts?.[profile.cluster_id] || 0} records
                                            </span>
                                        )}
                                    </div>
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

                    <FixedActionBar>
                        <Button type="normal" disabled={isProcessing} label="Back" onClick={() => setStep(step - 1)} />
                        {Object.keys(segmentCounts).length === 0 && (
                            <Button type="normal" disabled={isProcessing} label="Generate Segments" onClick={genrateSegments} />
                        )}
                        <Button type="normal" label="Next" disabled={!files.financeFile} onClick={() => setStep(step + 1)} />
                    </FixedActionBar>
                </div>
            )}

            {step === 4 && <Discounts />}
        </>
    );
}
