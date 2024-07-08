// app/components/ContextDetails.tsx
import React, { useState } from 'react';
import { ContextDetail } from '../types';

interface ContextDetailsProps {
  context: ContextDetail[];
}

const ContextDetails: React.FC<ContextDetailsProps> = ({ context }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="mt-2 text-sm">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-blue-500 hover:text-blue-700 focus:outline-none"
      >
        {isOpen ? 'Hide Citations' : 'Show Citations'}
      </button>
      {isOpen && (
        <div className="mt-2 p-2 bg-gray-100 rounded-md">
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
