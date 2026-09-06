import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/styles/globals.css";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Soft Skills AI · Análisis No Supervisado",
  description: "Plataforma de análisis no supervisado de habilidades blandas por elementos.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className={`${inter.variable} font-sans`}>
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex-1 min-w-0">
            <Topbar />
            <main className="px-4 sm:px-8 lg:px-10 py-8 max-w-[1400px] mx-auto">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}