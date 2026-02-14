export interface Job {
  id: string;
  title: string;
  company: string;
  city: string;
  state: string;
  country: string;
  remote: boolean;
  description: string;
  category: string;
  jobType: string;
  experience: string;
  education: string;
  url: string;
}

export interface Recommendation {
  id: string;
  score: number;
}

export type RecommendationMap = Record<string, Recommendation[]>;
