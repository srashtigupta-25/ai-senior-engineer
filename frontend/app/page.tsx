"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  askRepository,
  getArchitecture,
  getOnboarding,
  indexRepository,
} from "@/lib/api";

type RepositoryInfo = {
  repository: {
    repo_name: string;
    repo_url: string;
  };
  files: number;
  chunks: number;
  status: string;
};

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("https://github.com/pallets/flask");
  const [question, setQuestion] = useState("How does routing work in Flask?");
  const [activeTab, setActiveTab] = useState("chat");
  const [loading, setLoading] = useState(false);
  const [repoInfo, setRepoInfo] = useState<RepositoryInfo | null>(null);
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<string[]>([]);
  const [architecture, setArchitecture] = useState("");
  const [onboarding, setOnboarding] = useState("");

  async function handleIndex() {
    setLoading(true);

    try {
      const data = await indexRepository(repoUrl);
      setRepoInfo(data);
      setAnswer("");
      setSources([]);
      setArchitecture("");
      setOnboarding("");
    } catch {
      alert("Repository indexing failed. Please check your backend terminal.");
    }

    setLoading(false);
  }

  async function handleAsk() {
    setLoading(true);

    try {
      const data = await askRepository(question);
      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch {
      alert("Question failed. Make sure backend and Ollama are running.");
    }

    setLoading(false);
  }

  async function handleArchitecture() {
    setLoading(true);

    try {
      const data = await getArchitecture();
      setArchitecture(data.architecture);
    } catch {
      alert("Architecture analysis failed.");
    }

    setLoading(false);
  }

  async function handleOnboarding() {
    setLoading(true);

    try {
      const data = await getOnboarding();
      setOnboarding(data.guide);
    } catch {
      alert("Onboarding guide failed.");
    }

    setLoading(false);
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto max-w-6xl px-6 py-10">
        <div className="mb-10">
          <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-cyan-400">
            Codebase Intelligence Platform
          </p>

          <h1 className="text-5xl font-bold tracking-tight">
            AI Senior Engineer
          </h1>

          <p className="mt-4 max-w-3xl text-lg text-slate-300">
            Paste a GitHub repository and let an AI system index the codebase,
            retrieve relevant files, explain architecture, answer engineering
            questions, and generate onboarding guidance.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
          <label className="mb-2 block text-sm text-slate-300">
            GitHub Repository URL
          </label>

          <div className="flex flex-col gap-3 md:flex-row">
            <input
              value={repoUrl}
              onChange={(event) => setRepoUrl(event.target.value)}
              className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
            />

            <button
              onClick={handleIndex}
              className="rounded-xl bg-cyan-500 px-6 py-3 font-semibold text-slate-950 hover:bg-cyan-400"
            >
              {loading ? "Working..." : "Analyze Repo"}
            </button>
          </div>

          {repoInfo && (
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              <Metric label="Repository" value={repoInfo.repository.repo_name} />
              <Metric label="Files Indexed" value={repoInfo.files} />
              <Metric label="Chunks Stored" value={repoInfo.chunks} />
            </div>
          )}
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          <TabButton
            label="Ask Senior Engineer"
            id="chat"
            activeTab={activeTab}
            setActiveTab={setActiveTab}
          />

          <TabButton
            label="Architecture"
            id="architecture"
            activeTab={activeTab}
            setActiveTab={setActiveTab}
          />

          <TabButton
            label="Onboarding"
            id="onboarding"
            activeTab={activeTab}
            setActiveTab={setActiveTab}
          />
        </div>

        <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          {activeTab === "chat" && (
            <div>
              <h2 className="mb-4 text-2xl font-bold">Ask Senior Engineer</h2>

              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                className="h-28 w-full rounded-xl border border-slate-700 bg-slate-950 p-4 text-white outline-none"
              />

              <button
                onClick={handleAsk}
                className="mt-4 rounded-xl bg-cyan-500 px-6 py-3 font-semibold text-slate-950 hover:bg-cyan-400"
              >
                {loading ? "Thinking..." : "Ask"}
              </button>

              {answer && (
                <>
                  <MarkdownBlock content={answer} />
                  <SourcesList sources={sources} />
                </>
              )}
            </div>
          )}

          {activeTab === "architecture" && (
            <div>
              <h2 className="mb-4 text-2xl font-bold">
                Architecture Analysis
              </h2>

              <button
                onClick={handleArchitecture}
                className="rounded-xl bg-cyan-500 px-6 py-3 font-semibold text-slate-950 hover:bg-cyan-400"
              >
                {loading ? "Analyzing..." : "Generate Architecture"}
              </button>

              {architecture && <MarkdownBlock content={architecture} />}
            </div>
          )}

          {activeTab === "onboarding" && (
            <div>
              <h2 className="mb-4 text-2xl font-bold">
                Developer Onboarding Guide
              </h2>

              <button
                onClick={handleOnboarding}
                className="rounded-xl bg-cyan-500 px-6 py-3 font-semibold text-slate-950 hover:bg-cyan-400"
              >
                {loading ? "Building Guide..." : "Generate Guide"}
              </button>

              {onboarding && <MarkdownBlock content={onboarding} />}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-1 text-2xl font-bold">{value}</p>
    </div>
  );
}

function SourcesList({ sources }: { sources: string[] }) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-4">
      <p className="text-sm font-semibold text-slate-300">Retrieved sources</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {sources.slice(0, 16).map((source) => (
          <span
            key={source}
            className="rounded-lg border border-slate-700 px-3 py-1 text-sm text-slate-300"
          >
            {source}
          </span>
        ))}
      </div>
    </div>
  );
}

function TabButton({
  label,
  id,
  activeTab,
  setActiveTab,
}: {
  label: string;
  id: string;
  activeTab: string;
  setActiveTab: (id: string) => void;
}) {
  return (
    <button
      onClick={() => setActiveTab(id)}
      className={`rounded-xl px-5 py-3 font-semibold ${
        activeTab === id
          ? "bg-cyan-500 text-slate-950"
          : "bg-slate-900 text-slate-300"
      }`}
    >
      {label}
    </button>
  );
}

function MarkdownBlock({ content }: { content: string }) {
  return (
    <div className="mt-6 rounded-xl border border-slate-800 bg-slate-950 p-6 text-slate-200">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
