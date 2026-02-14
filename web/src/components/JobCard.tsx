import Link from "next/link";
import { Job } from "@/lib/types";
import Badge from "./Badge";

interface JobCardProps {
  job: Job;
  compact?: boolean;
}

export default function JobCard({ job, compact = false }: JobCardProps) {
  const location = [job.city, job.state, job.country].filter(Boolean).join(", ");

  return (
    <Link href={`/jobs/${job.id}`}>
      <div className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition-all bg-white">
        <div>
          <h3 className="font-semibold text-gray-900 truncate">{job.title}</h3>
          <p className="text-sm text-gray-600 mt-0.5">{job.company}</p>
        </div>

        <div className="mt-2 flex items-center gap-1.5 text-sm text-gray-500">
          <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span className="truncate">{location}</span>
          {job.remote && <Badge variant="remote">Remote</Badge>}
        </div>

        {!compact && (
          <div className="mt-2.5 flex flex-wrap gap-1.5">
            <Badge variant="blue">{job.category}</Badge>
            <Badge variant="green">{job.jobType}</Badge>
            {job.experience && job.experience !== "Not Specified" && (
              <Badge variant="purple">{job.experience}</Badge>
            )}
          </div>
        )}
      </div>
    </Link>
  );
}
