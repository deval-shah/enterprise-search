import React, { useState } from 'react';
import { ContextDetail } from '../types';

interface ContextDetailsProps {
  context: ContextDetail[];
}

const ContextDetails: React.FC<ContextDetailsProps> = ({ context }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (context.length === 0) return null;

  return (
    <div className="mt-2 text-sm">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-blue-500 hover:text-blue-700 focus:outline-none"
      >
        {isOpen ? 'Hide Sources' : 'Show Sources'}
      </button>
      {isOpen && (
        <div className="mt-2 p-2 bg-gray-100 rounded-md">
          {/* <h4 className="font-semibold">Citations:</h4> */}
          <ol className="list-decimal list-inside">
            {context.map((detail, index) => (
              <li key={index} className="truncate">{detail.file_name}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
};

export default ContextDetails;