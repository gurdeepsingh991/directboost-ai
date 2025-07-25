import { Outlet, useOutletContext } from 'react-router'
import './App.css'
import Header from './components/shared/Header'
import { usePersistentState } from './hooks/usePersistanceStorage'

type ContextType = {
  email: string;
  setEmail: (value: string) => void;
};

function App() {
  const [email, setEmail] = usePersistentState<string>('email', '')

  return (
    <>
      <Header />
      <div className="bg-slate-50 min-h-screen text-slate-800 font-poppins">
        <Outlet context={{ email, setEmail }}>
        </Outlet>
      </div >

    </>

  )
}
export default App

export function useEmail() {
  return useOutletContext<ContextType>();
}
