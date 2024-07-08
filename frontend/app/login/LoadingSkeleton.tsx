// app/login/LoadingSkeleton.tsx

export default function LoadingSkeleton() {
    return (
      <div className="p-6 space-y-4 md:space-y-6 sm:p-8 animate-pulse">
        <div className="h-8 bg-gray-200 rounded dark:bg-gray-700 w-1/2 mb-4"></div>
        <div className="space-y-4">
          <div className="h-4 bg-gray-200 rounded dark:bg-gray-700 w-full"></div>
          <div className="h-10 bg-gray-200 rounded dark:bg-gray-700 w-full"></div>
          <div className="h-4 bg-gray-200 rounded dark:bg-gray-700 w-full"></div>
          <div className="h-10 bg-gray-200 rounded dark:bg-gray-700 w-full"></div>
          <div className="h-10 bg-gray-200 rounded dark:bg-gray-700 w-full"></div>
        </div>
      </div>
    );
  }
  