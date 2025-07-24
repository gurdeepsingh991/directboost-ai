
interface StepperProps{
    step:number
}

export default function Stepper({ step }:StepperProps) {
    const steps = ["Upload Booking", "Upload Finance", "Segmentation", "Discounts", "Email Preview", "Send Emails"];
    return (
        <div className="flex pt-26 justify-between mb-6 w-full max-w-2xl mx-auto opacity-80">
            {steps.map((stepName, index) => (
                <div key={index} className="flex-1 text-center relative">
                    <div
                        className={`rounded-full w-6 h-6 mx-auto mb-1 flex items-center justify-center text-sm font-bold 
            ${index < step ? "bg-blue-500 text-white" : "bg-gray-300 text-gray-600"}`}
                    >
                        {index + 1}
                    </div>
                    <p className="text-xs font-medium text-gray-700">{stepName}</p>
                    {index < steps.length - 1 && (
                        <div className="absolute top-3 right-[-50%] w-full h-0.5 bg-gray-300 z-[-1]" />
                    )}
                </div>
            ))}
        </div>
    )
}
