// import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import Home from './pages/home/Home.tsx'
import About from './pages/about/About.tsx';

import {
  createBrowserRouter,
  RouterProvider,
} from "react-router";

const router = createBrowserRouter([
  {
    path: "/",
    Component: App,
    children: [
      { index: true, Component: Home },
      { path: "about", Component: About },
      // {
      //   path: "auth",
      //   Component: AuthLayout,
      //   children: [
      //     { path: "login", Component: Login },
      //     { path: "register", Component: Register },
      //   ],
      // },
      // {
      //   path: "concerts",
      //   children: [
      //     { index: true, Component: ConcertsHome },
      //     { path: ":city", Component: ConcertsCity },
      //     { path: "trending", Component: ConcertsTrending },
      //   ],
      // },
    ],
  },
]);



createRoot(document.getElementById('root')!).render(
  <RouterProvider router={router}>
  </RouterProvider>,
)
