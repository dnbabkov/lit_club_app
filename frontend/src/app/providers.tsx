import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {AuthProvider} from "../auth/AuthContext.tsx";

type ProvidersProps = {
    children: ReactNode
}

const queryClient = new QueryClient()

export function Providers({ children }: ProvidersProps) {
    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>{children}</AuthProvider>
        </QueryClientProvider>
    )
}