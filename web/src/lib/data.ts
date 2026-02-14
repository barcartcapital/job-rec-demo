import { Job, RecommendationMap } from "./types";
import fs from "fs";
import path from "path";

function readJsonFile<T>(filename: string): T {
  const filePath = path.join(process.cwd(), "public", "data", filename);
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as T;
}

let _jobs: Job[] | null = null;
let _baselineRecs: RecommendationMap | null = null;
let _weightedRecs: RecommendationMap | null = null;

export function getJobs(): Job[] {
  if (!_jobs) {
    _jobs = readJsonFile<Job[]>("jobs.json");
  }
  return _jobs;
}

export function getBaselineRecs(): RecommendationMap {
  if (!_baselineRecs) {
    _baselineRecs = readJsonFile<RecommendationMap>("recs_baseline.json");
  }
  return _baselineRecs;
}

export function getWeightedRecs(): RecommendationMap {
  if (!_weightedRecs) {
    _weightedRecs = readJsonFile<RecommendationMap>("recs_weighted.json");
  }
  return _weightedRecs;
}

export function getJobById(id: string): Job | undefined {
  return getJobs().find((j) => j.id === id);
}
