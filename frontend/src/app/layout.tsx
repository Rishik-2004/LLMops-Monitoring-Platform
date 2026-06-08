import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/layout/Providers";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "LLMOps Platform – Enterprise LLM Monitoring",
  description:
    "Monitor, evaluate, and optimize your AI applications with production-grade observability.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans`}>
        <Providers>
          {children}
          <Toaster
            theme="dark"
            position="bottom-right"
            toastOptions={{
              style: {
                background: "hsl(222 47% 8%)",
                border: "1px solid hsl(222 47% 14%)",
                color: "hsl(210 40% 96%)",
              },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
