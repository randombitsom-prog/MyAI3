import { createBrowserRouter } from "react-router";
import LoginPage from "../components/LoginPage";
import Dashboard from "../components/Dashboard";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: LoginPage,
  },
  {
    path: "/dashboard",
    Component: Dashboard,
  },
]);
