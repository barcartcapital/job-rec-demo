import { notFound } from "next/navigation";
import Link from "next/link";
import {
  getJobs,
  getJobById,
  getBaselineRecs,
  getWeightedRecs,
} from "@/lib/data";
import { Job } from "@/lib/types";
import Badge from "@/components/Badge";
import RecommendationPanel from "@/components/RecommendationPanel";

export async function generateStaticParams() {
  const jobs = getJobs();
  return jobs.map((job) => ({ id: job.id }));
}

interface JobPageProps {
  params: Promise<{ id: string }>;
}

export default async function JobPage({ params }: JobPageProps) {
  const { id } = await params;
  const job = getJobById(id);

  if (!job) return notFound();

  const baselineRecs = getBaselineRecs();
  const weightedRecs = getWeightedRecs();

  const baseRecs = baselineRecs[id] || [];
  const wtdRecs = weightedRecs[id] || [];

  // Only fetch the specific jobs needed for recommendations (not all 1000)
  const neededIds = new Set([
    ...baseRecs.map((r) => r.id),
    ...wtdRecs.map((r) => r.id),
  ]);
  const allJobs = getJobs();
  const recJobs: Job[] = allJobs.filter((j) => neededIds.has(j.id));

  const baseRecIds = new Set(baseRecs.map((r) => r.id));
  const wtdRecIds = new Set(wtdRecs.map((r) => r.id));

  const overlap = [...baseRecIds].filter((rid) => wtdRecIds.has(rid)).length;

  const location = [job.city, job.state, job.country].filter(Boolean).join(", ");

  return (
    <div>
      {/* Back link */}
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-blue-600 mb-6"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to all jobs
      </Link>

      {/* Job Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{job.title}</h1>
            <p className="text-lg text-gray-600 mt-1">{job.company}</p>
            <div className="flex items-center gap-2 mt-2 text-gray-500">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>{location}</span>
            </div>
            <div className="flex flex-wrap gap-2 mt-3">
              <Badge variant="blue">{job.category}</Badge>
              <Badge variant="green">{job.jobType}</Badge>
              {job.remote && <Badge variant="remote">Remote</Badge>}
              {job.experience && job.experience !== "Not Specified" && (
                <Badge variant="purple">{job.experience}</Badge>
              )}
              {job.education && job.education !== "Not Specified" && (
                <Badge variant="orange">{job.education}</Badge>
              )}
            </div>
          </div>
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm shrink-0"
          >
            Apply on Workable
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        </div>

        {/* Description */}
        <div className="mt-6 pt-6 border-t border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            Job Description
          </h2>
          <div
            className="prose prose-sm max-w-none text-gray-700 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_li]:mb-1 [&_h3]:text-base [&_h3]:font-semibold [&_h3]:mt-4 [&_h3]:mb-2 [&_p]:mb-3"
            dangerouslySetInnerHTML={{ __html: job.description }}
          />
        </div>
      </div>

      {/* Recommendations */}
      <div className="mb-4">
        <h2 className="text-xl font-bold text-gray-900">
          Similar Job Recommendations
        </h2>
        <p className="text-gray-600 mt-1 text-sm">
          Comparing two recommendation approaches. Yellow bar = unique to that
          model. Overlap: {overlap}/{baseRecs.length} shared.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <RecommendationPanel
          title="Baseline Model"
          description="Recommends jobs with similar titles using TF-IDF cosine similarity on job titles only."
          recommendations={baseRecs}
          jobs={recJobs}
          colorClass="border-blue-500"
          otherRecIds={wtdRecIds}
        />
        <RecommendationPanel
          title="Enhanced Model"
          description="Combines description similarity (35%), title (25%), category (15%), location (10%), job type (8%), and experience level (7%)."
          recommendations={wtdRecs}
          jobs={recJobs}
          colorClass="border-emerald-500"
          otherRecIds={baseRecIds}
        />
      </div>

      {/* Legend */}
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 text-sm text-gray-600">
        <div className="font-semibold text-gray-800 mb-2">How to read this comparison:</div>
        <ul className="space-y-1">
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-4 bg-yellow-400 rounded shrink-0" />
            Yellow bar indicates a recommendation unique to that model (not in the other)
          </li>
          <li className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-blue-500 shrink-0" />
            <strong>Baseline</strong> uses only job title similarity
          </li>
          <li className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-emerald-500 shrink-0" />
            <strong>Enhanced</strong> uses description + title + category + location + job type + experience level
          </li>
        </ul>
      </div>
    </div>
  );
}
