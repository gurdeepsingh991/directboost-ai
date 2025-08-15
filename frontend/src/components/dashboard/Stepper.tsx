
interface StepperProps {
    step: number
}

export default function Stepper({ step }: StepperProps) {
    const steps = ["Upload Booking", "Upload Finance", "Segmentation", "Discounts", "Email Preview", "Send Emails"];
    return (
        <div className="flex pt-20 justify-between mb-6 w-full  mx-auto opacity-90
          fixed inset-x-0  z-40
          border-t border-gray-200
          bg-white/90 backdrop-blur supports-[backdrop-filter]:bg-white/70
          shadow-[0_-6px_12px_-8px_rgba(0,0,0,0.15)]
        ">
            {steps.map((stepName, index) => {
                const isCompleted = index < step - 1;
                const isActive = index === step - 1;

                return (
                    <div key={index} className="flex-1 text-center relative">
                        <div
                            className={`rounded-full w-6 h-6 mx-auto mb-1 flex items-center justify-center text-sm font-bold
          ${isCompleted ? "bg-blue-600 text-white" : isActive ? "bg-blue-400 text-white animate-pulse" : "bg-gray-300 text-gray-600"}`}
                        >
                            {index + 1}
                        </div>
                        <p className="text-xs font-medium text-gray-700">{stepName}</p>

                        {index < steps.length - 1 && (
                            <div
                                className={`absolute top-3 left-1/2 w-full h-0.5 z-[-1] ${index < step - 1 ? "bg-blue-400" : "bg-gray-300"}`}
                            />
                        )}
                    </div>
                );
            })}
        </div>
    )
}
