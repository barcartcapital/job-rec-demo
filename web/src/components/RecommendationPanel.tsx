import { Job, Recommendation } from "@/lib/types";
import JobCard from "./JobCard";

interface RecommendationPanelProps {
  title: string;
  description: string;
  recommendations: Recommendation[];
  jobs: Job[];
  colorClass: string;
  otherRecIds: Set<string>;
}

export default function RecommendationPanel({
  title,
  description,
  recommendations,
  jobs,
  colorClass,
  otherRecIds,
}: RecommendationPanelProps) {
  const jobMap = new Map(jobs.map((j) => [j.id, j]));

  return (
    <div className={`border-t-4 ${colorClass} rounded-lg bg-white shadow-sm`}>
      <div className="p-4 border-b border-gray-100">
        <h3 className="font-bold text-lg text-gray-900">{title}</h3>
        <p className="text-sm text-gray-500 mt-1">{description}</p>
      </div>
      <div className="p-4 space-y-3">
        {recommendations.map((rec) => {
          const job = jobMap.get(rec.id);
          if (!job) return null;

          const isUnique = !otherRecIds.has(rec.id);

          return (
            <div key={rec.id} className="relative">
              {isUnique && (
                <div className="absolute -left-1 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-yellow-400 rounded-r" title="Unique to this model" />
              )}
              <JobCard job={job} compact />
            </div>
          );
        })}
      </div>
    </div>
  );
}
