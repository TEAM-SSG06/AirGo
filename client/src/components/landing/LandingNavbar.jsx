import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Sparkles, Menu, X, ExternalLink, Sun, Moon } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

export const LandingNavbar = () => {
  const navigate = useNavigate();
  const { isDark, toggleTheme } = useTheme();
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 15);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { name: "The Challenge", href: "#challenge" },
    { name: "How It Works", href: "#how-it-works" },
    { name: "AI Insights", href: "#ai-insights", hasSparkle: true },
    { name: "Capabilities", href: "#capabilities" },
    { name: "Roadmap", href: "#roadmap" },
  ];

  const handleNavClick = (e, href) => {
    e.preventDefault();
    setMobileMenuOpen(false);
    const target = document.querySelector(href);
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <header
      className={`sticky top-0 z-50 w-full transition-all duration-200 ${
        isScrolled
          ? "bg-white/95 dark:bg-[#0d1322]/95 backdrop-blur-md border-b border-slate-200/90 dark:border-slate-800 shadow-xs"
          : "bg-white/90 dark:bg-[#0d1322]/90 backdrop-blur-sm border-b border-slate-200/60 dark:border-slate-800/60"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14 sm:h-16 py-1.5 sm:py-2">
          {/* Brand Logo */}
          <div
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            className="flex items-center gap-2.5 sm:gap-3 cursor-pointer group select-none"
          >
            <div className="w-8.5 h-8.5 sm:w-9 sm:h-9 rounded-lg bg-slate-950 dark:bg-blue-600 text-white flex items-center justify-center font-bold text-xs sm:text-sm tracking-wider shadow-xs group-hover:bg-blue-600 transition-colors">
              AG
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-slate-900 dark:text-white text-sm sm:text-base tracking-tight group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors whitespace-nowrap">
                  AirGo
                </span>
                <span className="inline-flex items-center px-1.5 py-0.2 rounded text-[9.5px] font-semibold bg-blue-50 dark:bg-blue-950/80 text-blue-700 dark:text-blue-300 border border-blue-200/60 dark:border-blue-800/80">
                  APIx
                </span>
              </div>
              <p className="text-[10px] sm:text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-none mt-0.5 whitespace-nowrap">
                India Airfare Price Index Platform
              </p>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center gap-6 text-[13px] font-medium text-slate-600 dark:text-slate-300">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                onClick={(e) => handleNavClick(e, link.href)}
                className={`py-1 transition-colors hover:text-blue-600 dark:hover:text-blue-400 ${
                  link.hasSparkle ? "inline-flex items-center gap-1 text-blue-600 dark:text-blue-400 font-semibold" : ""
                }`}
              >
                {link.hasSparkle && <Sparkles className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />}
                <span>{link.name}</span>
              </a>
            ))}
            <button
              onClick={() => navigate("/index-methodology")}
              className="py-1 text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer"
            >
              Methodology
            </button>
          </nav>

          {/* Action CTA & Dark Mode Toggle & Mobile Hamburger */}
          <div className="flex items-center gap-2 sm:gap-2.5">
            {/* Dark Mode Toggle */}
            <button
              onClick={toggleTheme}
              title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
              className="p-1.5 sm:p-2 rounded-lg text-slate-600 dark:text-amber-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
            </button>

            <button
              onClick={() => navigate("/dashboard")}
              className="flex items-center gap-1.5 px-3.5 py-1.5 sm:px-4 sm:py-2 rounded-lg bg-blue-600 hover:bg-blue-700 active:scale-[0.98] text-white text-xs sm:text-[13px] font-medium shadow-xs hover:shadow transition-all cursor-pointer group whitespace-nowrap"
            >
              <span>Explore Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>

            {/* Mobile Toggle Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-1.5 rounded-lg text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-4.5 h-4.5" /> : <Menu className="w-4.5 h-4.5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-200/80 bg-white/98 backdrop-blur-md px-4 sm:px-6 py-4 shadow-lg animate-in fade-in slide-in-from-top-2 duration-150">
          <div className="flex flex-col gap-2">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                onClick={(e) => handleNavClick(e, link.href)}
                className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-700 hover:text-blue-600 hover:bg-blue-50/70 transition-colors"
              >
                {link.hasSparkle && <Sparkles className="w-4 h-4 text-blue-600" />}
                <span>{link.name}</span>
              </a>
            ))}
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                navigate("/index-methodology");
              }}
              className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-700 hover:text-blue-600 hover:bg-blue-50/70 transition-colors text-left"
            >
              Methodology & Formulas
            </button>
            <div className="pt-2 mt-1 border-t border-slate-100 flex flex-col gap-2">
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  navigate("/index-apix");
                }}
                className="flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
              >
                <span>Live Route Index (APIx)</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  navigate("/data-collection");
                }}
                className="flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
              >
                <span>Live Data Collection & Proof</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
