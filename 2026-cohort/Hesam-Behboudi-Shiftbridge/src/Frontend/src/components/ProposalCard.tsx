import { Calendar, Check, CheckCircle } from "lucide-react";
import type { ProposalType } from "../types";

export   const ProposalCard = ({ proposal,currentRole,handleApproveProposal }: { proposal: ProposalType,currentRole:string,handleApproveProposal:(id:string)=>void }) => {
    const data = proposal.new_shift_data;
    const isManager = currentRole === 'manager';
    const isCurrentRoleApproved = isManager ? proposal.isManagerApproved : proposal.isWorkerApproved;

    return (
      <div className="bg-white border border-indigo-100 rounded-2xl p-4 shadow-xs space-y-3 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between border-b border-slate-100 pb-2">
          <div className="flex items-center gap-2">
            <span className="p-1.5 bg-indigo-50 text-indigo-600 rounded-lg">
              <Calendar className="w-4 h-4" />
            </span>
            <span className="text-xs font-bold text-slate-800">Proposal #{proposal.id}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium flex items-center gap-1 ${proposal.isManagerApproved ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>
              {proposal.isManagerApproved && <CheckCircle className="w-3 h-3" />}
              {!isManager && <>
                Manager: {proposal.isManagerApproved ? 'Approved' : 'Pending'}
              </>
              }
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-2.5 rounded-xl border border-slate-100">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-semibold">Current</span>
            <span className="font-medium text-slate-700">{data.current_day} @ {data.current_start_time}</span>
            <span className="text-slate-500 block text-[11px]">{data.current_length}h</span>
          </div>
          <div>
            <span className="text-indigo-400 block text-[10px] uppercase font-semibold">Proposed</span>
            <span className="font-medium text-indigo-700">{data.proposed_day} @ {data.proposed_start_time}</span>
            <span className="text-indigo-600 block text-[11px]">{data.proposed_length}h</span>
          </div>
        </div>

        {data.note && (
          <p className="text-xs text-slate-600 italic bg-amber-50/50 p-2 rounded-lg border border-amber-100/50">
            "{data.note}"
          </p>
        )}

        <div className="flex items-center justify-end gap-2 pt-1">
          {!isCurrentRoleApproved ? (
            <button
              onClick={() => {
                console.error(proposal)
                handleApproveProposal(proposal.id!);
              }}
              className="px-3 py-1.5 text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-2xs transition-colors flex items-center gap-1 cursor-pointer"
            >
              <Check className="w-3.5 h-3.5" /> Approve
            </button>
          ) : (
            <span className="text-xs text-emerald-600 font-medium flex items-center gap-1 bg-emerald-50 px-2.5 py-1 rounded-lg">
              <CheckCircle className="w-3.5 h-3.5" /> Approved
            </span>
          )}
        </div>
      </div>
    );
  };
