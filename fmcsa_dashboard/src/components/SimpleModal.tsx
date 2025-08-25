import React from 'react';

interface SimpleModalProps {
  isOpen: boolean;
  onClose: () => void;
  carrier: any;
}

const SimpleModal: React.FC<SimpleModalProps> = ({ isOpen, onClose, carrier }) => {
  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center"
      style={{ zIndex: 9999 }}
      onClick={onClose}
    >
      <div 
        className="bg-white p-6 rounded-lg shadow-xl"
        style={{ maxWidth: '500px', margin: '20px' }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-2xl font-bold mb-4">Carrier Details</h2>
        <p className="mb-2"><strong>USDOT:</strong> {carrier?.usdot_number}</p>
        <p className="mb-2"><strong>Name:</strong> {carrier?.legal_name}</p>
        <p className="mb-2"><strong>Location:</strong> {carrier?.physical_city}, {carrier?.physical_state}</p>
        <button
          onClick={onClose}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default SimpleModal;