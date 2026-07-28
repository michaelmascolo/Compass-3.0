import { MessageSquareHeart } from "lucide-react";

// Persistent "Help Improve Compass" affordance, available throughout the experience.
export default function FeedbackButton({ onClick }) {
  return (
    <button
      onClick={onClick}
      data-testid="help-improve-compass-button"
      className="fixed bottom-5 right-5 z-40 inline-flex items-center gap-2 bg-white/90 backdrop-blur border border-stone-300 text-stone-700 px-4 py-2.5 rounded-full shadow-sm hover:border-[#8C3A2A] hover:text-[#8C3A2A] hover:-translate-y-px transition-[transform,color,border-color] text-[13px] font-medium"
    >
      <MessageSquareHeart className="h-4 w-4" />
      Can We Ask a Favor?
    </button>
  );
}
