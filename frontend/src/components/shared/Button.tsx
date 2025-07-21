interface ButtonProps {
    type?: 'normal' | 'cancel' | 'delete';
    label?: string;
    onClick?: () => void;
  }
  
  export default function Button({ type = 'normal', label = 'Get Started', onClick }: ButtonProps) {
    const buttonTypes = {
      normal: {
        buttonColor: 'bg-blue-600',
        borderColor: 'border-blue-700',
        hoverColor: 'hover:bg-blue-500',
        ringColor: 'focus:ring-blue-400',
      },
      cancel: {
        buttonColor: 'bg-gray-300',
        borderColor: 'border-gray-400',
        hoverColor: 'hover:bg-gray-400',
        ringColor: 'focus:ring-gray-300',
      },
      delete: {
        buttonColor: 'bg-red-600',
        borderColor: 'border-red-700',
        hoverColor: 'hover:bg-red-500',
        ringColor: 'focus:ring-red-400',
      },
    };
  
    const styles = buttonTypes[type];
  
    return (
      <button
        onClick={onClick}
        className={`
          ${styles.buttonColor} 
          ${styles.borderColor} 
          ${styles.hoverColor}
          ${styles.ringColor}
          text-white px-5 py-2 rounded-xl 
          border transition-all duration-200 
          font-semibold shadow-sm hover:shadow-md 
          focus:outline-none focus:ring-2
          cursor-pointer
        `}
      >
        {label}
      </button>
    );
  }
  