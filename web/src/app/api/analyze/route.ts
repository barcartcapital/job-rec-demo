import { NextRequest, NextResponse } from "next/server";

interface JobSummary {
  title: string;
  company: string;
  city: string;
  country: string;
  category: string;
  jobType: string;
  experience: string;
}

interface AnalyzeRequest {
  sourceJob: JobSummary;
  baselineRecs: JobSummary[];
  enhancedRecs: JobSummary[];
}

export async function POST(request: NextRequest) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: "OPENAI_API_KEY not configured" },
      { status: 500 }
    );
  }

  const body: AnalyzeRequest = await request.json();
  const { sourceJob, baselineRecs, enhancedRecs } = body;

  const prompt = `You are an expert in job recommendation systems. A user is currently viewing a job listing and two recommendation models are suggesting similar jobs. Analyze which model provides better recommendations for the user.

## Source Job (the job the user is viewing)
- Title: ${sourceJob.title}
- Company: ${sourceJob.company}
- Location: ${sourceJob.city}, ${sourceJob.country}
- Category: ${sourceJob.category}
- Type: ${sourceJob.jobType}
- Experience: ${sourceJob.experience}

## Baseline Model Recommendations (uses only job title similarity)
${baselineRecs.map((r, i) => `${i + 1}. ${r.title} at ${r.company} (${r.city}, ${r.country}) [${r.category}, ${r.jobType}, ${r.experience}]`).join("\n")}

## Enhanced Model Recommendations (uses description + title + category + location + job type + experience)
${enhancedRecs.map((r, i) => `${i + 1}. ${r.title} at ${r.company} (${r.city}, ${r.country}) [${r.category}, ${r.jobType}, ${r.experience}]`).join("\n")}

Provide a concise analysis (3-5 sentences) covering:
1. Which model produced more relevant recommendations for this specific job and why
2. Any notable strengths or weaknesses you see in each model's picks
3. Your verdict: which model wins for user experience

Be specific — reference the actual job titles and explain your reasoning. Format your verdict clearly at the end as "Verdict: [Baseline/Enhanced] model wins" with a one-line reason.`;

  try {
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: prompt }],
        temperature: 0.3,
        max_tokens: 400,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      return NextResponse.json(
        { error: `OpenAI API error: ${response.status}` },
        { status: 502 }
      );
    }

    const data = await response.json();
    const analysis = data.choices?.[0]?.message?.content || "No analysis generated.";

    return NextResponse.json({ analysis });
  } catch (err) {
    return NextResponse.json(
      { error: "Failed to connect to OpenAI API" },
      { status: 502 }
    );
  }
}
