import { Outlet, useNavigate } from 'react-router'
import './App.css'
import Header from './components/shared/Header'
import { usePersistentState } from './hooks/usePersistanceStorage'
import { useEffect } from 'react'


function App() {
  const navigate = useNavigate();
  const [email] = usePersistentState<string>('email', '')
  useEffect(() => {
    if (email) {
      navigate('/dashboard')
    }
  }, [])
  return (
    <>
      <Header />
      <div className="bg-slate-50 min-h-screen text-slate-800 font-poppins">
        <Outlet>
        </Outlet>
      </div >

    </>

  )
}
export default App
