// import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import Home from './pages/Home.tsx'
import About from './pages/About.tsx'; 

import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import Login from './pages/Login.tsx';
import Dashboard from './pages/Dashboard.tsx';
 
const router = createBrowserRouter([
  {
    path: "/",
    Component: App,
    children: [
      { index: true, Component: Home },
      { path: "about", Component: About },
      { path: "login", Component: Login },
      {path:"dashboard", Component:Dashboard}
    ]
  }
]);



createRoot(document.getElementById('root')!).render(
  <RouterProvider router={router}>
  </RouterProvider>,
)
