interface ButtonProps {
    type?: 'normal' | 'cancel' | 'delete';
    label?: string;
    onClick?: () => void;
    disabled?:boolean
  }
  
  export default function Button({ type = 'normal', label = 'Get Started', onClick, disabled= false }: ButtonProps) {
    const buttonTypes = {
      normal: {
        buttonColor: 'bg-blue-500',
        borderColor: 'border-blue-600',
        hoverColor: 'hover:bg-blue-400',
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
        disabled={disabled}
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
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        {label}
      </button>
    );
  }
  