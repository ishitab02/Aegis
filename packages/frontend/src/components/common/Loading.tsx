export function Loading({ text = "Loading..." }: { text?: string }) {
  return (
    <div className="flex items-center justify-center p-8 text-gray-400">
      <div className="w-5 h-5 border-2 border-gray-600 border-t-aegis-accent rounded-full animate-spin mr-3" />
      {text}
    </div>
  );
}
