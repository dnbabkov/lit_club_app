import type { ReactNode } from "react";
import { NavBar } from "./NavBar"

type LayoutProps = {
    children: ReactNode
}

export function Layout({children} : LayoutProps) {
    return (
        <div>
            <NavBar/>
            <main style={{maxWidth: 1000, margin: "0 auto", padding: "24px 16px"}}>
                {children}
            </main>
        </div>
    )
}