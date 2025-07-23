import { Outlet } from 'react-router'
import './App.css'
import Header from './components/shared/Header'
import { useEffect } from 'react'
import apiUtils from './utils/apiUtils'


function App() {
  

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
