import { getJobs } from "@/lib/data";
import JobBrowser from "@/components/JobBrowser";

export default function Home() {
  const jobs = getJobs();

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Browse Jobs</h2>
        <p className="text-gray-600 mt-1">
          {jobs.length} jobs available. Click any job to see recommendations
          from two different models.
        </p>
      </div>
      <JobBrowser jobs={jobs} />
    </div>
  );
}
