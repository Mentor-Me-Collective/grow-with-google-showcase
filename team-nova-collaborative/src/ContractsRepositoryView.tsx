import React, { useState } from 'react';
import {
  FolderKanban,
  Search,
  Filter,
  Plus,
  FileText,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Download,
  Trash2,
  Eye,
  ChevronLeft,
  ChevronRight,
  MoreVertical,
  Paperclip,
  CreditCard
} from 'lucide-react';
import { Contract, ContractStatus, ContractPaymentStatus } from '../types';
import { formatOriginalCurrency } from '../utils/currency';

interface ContractsRepositoryViewProps {
  contracts: Contract[];
  onSelectContract: (contract: Contract) => void;
  onDeleteContract: (id: string) => void;
  onUpdatePaymentStatus?: (id: string, newStatus: ContractPaymentStatus) => void;
  openCreateModal: () => void;
  setActiveTab: (tab: string) => void;
}

export const ContractsRepositoryView: React.FC<ContractsRepositoryViewProps> = ({
  contracts,
  onSelectContract,
  onDeleteContract,
  onUpdatePaymentStatus,
  openCreateModal,
  setActiveTab
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [paymentStatusFilter, setPaymentStatusFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');

  const filteredContracts = contracts.filter((c) => {
    const matchesSearch =
      c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.clientName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'All' || c.status === statusFilter;
    const matchesPaymentStatus = paymentStatusFilter === 'All' || (c.paymentStatus || 'Unpaid') === paymentStatusFilter;
    const matchesType = typeFilter === 'All' || c.type === typeFilter;
    return matchesSearch && matchesStatus && matchesPaymentStatus && matchesType;
  });

  const getStatusBadge = (status: ContractStatus) => {
    switch (status) {
      case 'Signed':
        return (
          <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300/60 inline-flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Signed
          </span>
        );
      case 'Pending':
        return (
          <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-amber-100 text-amber-800 border border-amber-300/60 inline-flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-amber-600" />
            Pending Signature
          </span>
        );
      case 'Overdue':
        return (
          <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-rose-100 text-rose-800 border border-rose-300/60 inline-flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
            Overdue
          </span>
        );
      case 'Draft':
        return (
          <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-slate-100 text-slate-700 border border-slate-300 inline-flex items-center gap-1">
            <FileText className="w-3.5 h-3.5 text-slate-500" />
            Draft
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Primary Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div>
          <h1 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <FolderKanban className="w-5 h-5 text-emerald-600" />
            Contract Repository
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Central repository of all executed, pending, and draft legal documents.
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="px-4 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-md shadow-emerald-500/20 flex items-center gap-2 transition-all"
        >
          <Plus className="w-4 h-4 stroke-[3]" />
          <span>+ New Document</span>
        </button>
      </div>

      {/* Filter Controls Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by contract ID, document title, or client..."
            className="w-full pl-9 pr-4 py-2 bg-slate-50 text-xs text-slate-800 placeholder-slate-400 rounded-xl border border-slate-200 focus:border-emerald-500 focus:bg-white outline-none transition-all"
          />
        </div>

        {/* Dropdowns */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200 text-xs text-slate-600">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-semibold">Doc Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent text-slate-800 font-bold outline-none cursor-pointer"
            >
              <option value="All">All Statuses</option>
              <option value="Signed">Signed</option>
              <option value="Pending">Pending</option>
              <option value="Overdue">Overdue</option>
              <option value="Draft">Draft</option>
            </select>
          </div>

          <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200 text-xs text-slate-600">
            <CreditCard className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-semibold">Payment Status:</span>
            <select
              value={paymentStatusFilter}
              onChange={(e) => setPaymentStatusFilter(e.target.value)}
              className="bg-transparent text-slate-800 font-bold outline-none cursor-pointer"
            >
              <option value="All">All Payment Statuses</option>
              <option value="Unpaid">Unpaid</option>
              <option value="Deposit Paid">Deposit Paid</option>
              <option value="Partially Paid">Partially Paid</option>
              <option value="Fully Paid">Fully Paid</option>
              <option value="Overdue">Overdue</option>
            </select>
          </div>

          <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200 text-xs text-slate-600">
            <span className="font-semibold">Type:</span>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-transparent text-slate-800 font-bold outline-none cursor-pointer"
            >
              <option value="All">All Types</option>
              <option value="MSA">MSA</option>
              <option value="Tenancy Agreement">Tenancy Agreement</option>
              <option value="NDA">NDA</option>
              <option value="Custom Statement of Work">Custom SOW</option>
            </select>
          </div>
        </div>
      </div>

      {/* Repository Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-600">
            <thead className="bg-slate-100/80 text-slate-500 font-bold uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th className="py-3.5 px-5">Document ID & Title</th>
                <th className="py-3.5 px-5">Recipient / Client</th>
                <th className="py-3.5 px-5">Date Sent</th>
                <th className="py-3.5 px-5">Contract Value</th>
                <th className="py-3.5 px-5">Legal Status</th>
                <th className="py-3.5 px-5">Payment Status</th>
                <th className="py-3.5 px-5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredContracts.map((contract) => (
                <tr key={contract.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-4 px-5 font-semibold text-slate-900">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center font-bold shrink-0 border border-slate-200">
                        <FileText className="w-4 h-4 text-emerald-600" />
                      </div>
                      <div>
                        <p className="font-bold text-slate-900">{contract.title}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[10px] text-slate-400 font-mono">{contract.id}</span>
                          {contract.attachedFileName && (
                            <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px] font-semibold flex items-center gap-1 border border-emerald-200">
                              <Paperclip className="w-2.5 h-2.5" />
                              <span className="truncate max-w-[110px]">{contract.attachedFileName}</span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-5">
                    <p className="font-semibold text-slate-800">{contract.clientName}</p>
                    <p className="text-[10px] text-slate-400">{contract.clientEmail}</p>
                  </td>
                  <td className="py-4 px-5 text-slate-500 font-medium">{contract.dateCreated}</td>
                  <td className="py-4 px-5">
                    <p className="font-extrabold text-slate-900">${contract.value.toLocaleString()} <span className="text-[10px] text-slate-500 font-bold">USD</span></p>
                    {contract.originalCurrency && contract.originalCurrency !== 'USD' && contract.originalValue && (
                      <p className="text-[10px] font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200 inline-block mt-0.5">
                        {formatOriginalCurrency(contract.originalValue, contract.originalCurrency)}
                      </p>
                    )}
                    {(contract.initialValue || contract.subsequentValue) && (
                      <div className="mt-1 space-y-0.5 text-[10px] border-t border-slate-100 pt-1">
                        <div className="flex items-center gap-1 text-emerald-700 font-medium">
                          <span>Initial Deposit:</span>
                          <span className="font-bold">
                            {contract.originalCurrency && contract.originalCurrency !== 'USD' && contract.originalInitialValue
                              ? formatOriginalCurrency(contract.originalInitialValue, contract.originalCurrency)
                              : `$${(contract.initialValue || 0).toLocaleString()} USD`}
                          </span>
                        </div>
                        <div className="flex items-center gap-1 text-slate-500 font-medium">
                          <span>Subsequent:</span>
                          <span className="font-bold">
                            {contract.originalCurrency && contract.originalCurrency !== 'USD' && contract.originalSubsequentValue
                              ? formatOriginalCurrency(contract.originalSubsequentValue, contract.originalCurrency)
                              : `$${(contract.subsequentValue || 0).toLocaleString()} USD`}
                          </span>
                        </div>
                      </div>
                    )}
                  </td>
                  <td className="py-4 px-5">{getStatusBadge(contract.status)}</td>
                  <td className="py-4 px-5">
                    <div className="relative inline-block">
                      <select
                        value={contract.paymentStatus || 'Unpaid'}
                        onChange={(e) => onUpdatePaymentStatus?.(contract.id, e.target.value as ContractPaymentStatus)}
                        className={`px-2.5 py-1 text-xs font-extrabold rounded-full border outline-none cursor-pointer transition-all shadow-2xs ${
                          contract.paymentStatus === 'Fully Paid'
                            ? 'bg-emerald-100 text-emerald-900 border-emerald-300 hover:bg-emerald-200'
                            : contract.paymentStatus === 'Deposit Paid'
                            ? 'bg-blue-100 text-blue-900 border-blue-300 hover:bg-blue-200'
                            : contract.paymentStatus === 'Partially Paid'
                            ? 'bg-amber-100 text-amber-900 border-amber-300 hover:bg-amber-200'
                            : contract.paymentStatus === 'Overdue'
                            ? 'bg-rose-100 text-rose-900 border-rose-300 hover:bg-rose-200'
                            : 'bg-slate-100 text-slate-800 border-slate-300 hover:bg-slate-200'
                        }`}
                      >
                        <option value="Unpaid" className="bg-white text-slate-900 font-bold">Unpaid</option>
                        <option value="Deposit Paid" className="bg-white text-slate-900 font-bold">Deposit Paid</option>
                        <option value="Partially Paid" className="bg-white text-slate-900 font-bold">Partially Paid</option>
                        <option value="Fully Paid" className="bg-white text-slate-900 font-bold">Fully Paid</option>
                        <option value="Overdue" className="bg-white text-slate-900 font-bold">Overdue</option>
                      </select>
                    </div>
                  </td>
                  <td className="py-4 px-5 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => {
                          onSelectContract(contract);
                          setActiveTab('editor');
                        }}
                        className="p-2 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-semibold text-xs flex items-center gap-1 transition-colors"
                        title="Edit & Sign"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Edit / Sign</span>
                      </button>
                      <button
                        onClick={() => onDeleteContract(contract.id)}
                        className="p-2 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                        title="Delete Document"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between text-xs text-slate-500">
          <span>Showing 1-{filteredContracts.length} of {contracts.length} documents</span>
          <div className="flex items-center gap-2">
            <button className="p-1.5 rounded-lg border border-slate-200 hover:bg-white text-slate-600 disabled:opacity-50" disabled>
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-bold text-slate-800 px-2 py-0.5 rounded bg-white border border-slate-200">
              Page 1
            </span>
            <button className="p-1.5 rounded-lg border border-slate-200 hover:bg-white text-slate-600 disabled:opacity-50" disabled>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
