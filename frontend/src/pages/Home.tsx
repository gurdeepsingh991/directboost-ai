import { useNavigate } from "react-router-dom";
import Button from "../components/shared/Button";
import { usePersistentState } from "../hooks/usePersistanceStorage";
import { useEffect, useState } from "react";

export default function Home() {
  const [email, setEmail] = usePersistentState<string>('email', '')
  const navigate = useNavigate();
  const [isValidEmail, setIsValidEmail] = useState<boolean>(false)

  useEffect (()=>{
    if(email){
      navigate('/dashboard')
    }

  },[])

  const updateEmail = (enteredEmail: string) => {
    validateEmail(enteredEmail)
    setEmail(enteredEmail)
    console.log(enteredEmail)
  }

  const getStarted = () => {
    console.log("redirecting");
    navigate("/dashboard");
  };

  const validateEmail = (enteredEmail:string)=>{

    if(/^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/.test(enteredEmail)){
      setIsValidEmail(true)
    }
    else{
      setIsValidEmail(false)
    }

  }

  return (
    <>
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50 px-4 text-center">
        <h1 className="text-4xl font-bold text-blue-700 mb-4">Welcome to Direct Boost AI</h1>

        <p className="text-lg text-gray-700 max-w-2xl mb-2">
          Boost your hotel’s direct bookings with AI-powered personalised email campaigns.
        </p>

        <p className="text-md text-gray-600 mb-6">
          Enter your email address to get started.
        </p>

        <div className="w-full max-w-md">
          <label htmlFor="email" className="block text-left text-sm font-medium text-gray-700 mb-1">
            Email address
          </label>
          <input
            type="email"
            name="email"
            id="email"
            value={email}
            onChange={(e) => updateEmail(e.target.value)}
            className="w-full border-2 border-blue-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all"
            placeholder="you@example.com"
          />
        </div>

        <div className="mt-6">
          <Button disabled={!isValidEmail} type="normal" label="Get Started" onClick={getStarted} />
        </div>
      </div>

    </>
  )
}
