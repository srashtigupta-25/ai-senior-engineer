"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  Activity,
  ArrowRight,
  BookOpen,
  BrainCircuit,
  CheckCircle2,
  FileCode2,
  GitBranch,
  LayoutDashboard,
  Loader2,
  Network,
  Search,
  Sparkles,
} from "lucide-react";
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
  repository_type?: string;
  status: string;
};

type TabId = "chat" | "architecture" | "onboarding";
type PendingAction = "index" | "ask" | "architecture" | "onboarding" | null;

const tabs: Array<{
  id: TabId;
  label: string;
  icon: typeof BrainCircuit;
}> = [
  { id: "chat", label: "Ask", icon: BrainCircuit },
  { id: "architecture", label: "Architecture", icon: Network },
  { id: "onboarding", label: "Onboarding", icon: BookOpen },
];

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("https://github.com/pallets/flask");
  const [question, setQuestion] = useState("How does Flask work internally?");
  const [activeTab, setActiveTab] = useState<TabId>("chat");
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const [repoInfo, setRepoInfo] = useState<RepositoryInfo | null>(null);
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<string[]>([]);
  const [architecture, setArchitecture] = useState("");
  const [onboarding, setOnboarding] = useState("");
  const [error, setError] = useState("");

  const isBusy = pendingAction !== null;

  async function handleIndex() {
    setPendingAction("index");
    setError("");

    try {
      const data = await indexRepository(repoUrl);
      setRepoInfo(data);
      setAnswer("");
      setSources([]);
      setArchitecture("");
      setOnboarding("");
    } catch {
      setError("Repository indexing failed. Check the backend terminal and confirm the GitHub URL is public.");
    }

    setPendingAction(null);
  }

  async function handleAsk() {
    setPendingAction("ask");
    setError("");

    try {
      const data = await askRepository(question);
      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch {
      setError("Question failed. Confirm the backend and Ollama are running.");
    }

    setPendingAction(null);
  }

  async function handleArchitecture() {
    setPendingAction("architecture");
    setError("");

    try {
      const data = await getArchitecture();
      setArchitecture(data.architecture);
    } catch {
      setError("Architecture analysis failed. Re-index the repository and try again.");
    }

    setPendingAction(null);
  }

  async function handleOnboarding() {
    setPendingAction("onboarding");
    setError("");

    try {
      const data = await getOnboarding();
      setOnboarding(data.guide);
    } catch {
      setError("Onboarding guide failed. Re-index the repository and try again.");
    }

    setPendingAction(null);
  }

  return (
    <main className="min-h-screen bg-[#f5f7fb] text-[#111827]">
      <section className="border-b border-[#dfe5ee] bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-6 py-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex size-12 items-center justify-center rounded-lg bg-[#111827] text-white">
              <Sparkles size={24} />
            </div>
            <div>
              <p className="text-sm font-semibold uppercase text-[#0f766e]">
                Codebase Intelligence
              </p>
              <h1 className="text-3xl font-bold tracking-tight">
                AI Senior Engineer
              </h1>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <StatusPill label="FastAPI" value=":8000" />
            <StatusPill label="Next.js" value=":3001" />
            <StatusPill label="Ollama" value="local" />
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[380px_1fr]">
        <aside className="space-y-6">
          <div className="rounded-lg border border-[#dfe5ee] bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <GitBranch size={18} className="text-[#0f766e]" />
              <h2 className="text-lg font-semibold">Repository</h2>
            </div>

            <label className="mb-2 block text-sm font-medium text-[#4b5563]">
              GitHub URL
            </label>
            <input
              value={repoUrl}
              onChange={(event) => setRepoUrl(event.target.value)}
              className="w-full rounded-lg border border-[#cbd5e1] bg-white px-3 py-3 text-sm outline-none transition focus:border-[#0f766e] focus:ring-4 focus:ring-[#0f766e]/10"
            />

            <button
              onClick={handleIndex}
              disabled={isBusy}
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-[#111827] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#1f2937] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {pendingAction === "index" ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Search size={18} />
              )}
              Analyze Repository
            </button>

            {repoInfo && (
              <div className="mt-5 space-y-3">
                <Metric
                  icon={CheckCircle2}
                  label="Repository"
                  value={repoInfo.repository.repo_name}
                />
                <Metric
                  icon={LayoutDashboard}
                  label="Detected Type"
                  value={repoInfo.repository_type || "Indexed"}
                />
                <div className="grid grid-cols-2 gap-3">
                  <Metric icon={FileCode2} label="Files" value={repoInfo.files} />
                  <Metric icon={Activity} label="Chunks" value={repoInfo.chunks} />
                </div>
              </div>
            )}
          </div>

          <div className="rounded-lg border border-[#dfe5ee] bg-[#111827] p-5 text-white shadow-sm">
            <p className="text-sm font-semibold text-[#5eead4]">Demo Checks</p>
            <div className="mt-4 space-y-3 text-sm text-[#d1d5db]">
              <CheckItem text="Repository type should be framework/library for Flask." />
              <CheckItem text="Answers should cite relative paths like src/flask/app.py." />
              <CheckItem text="Architecture and onboarding should use their own report sections." />
            </div>
          </div>
        </aside>

        <section className="min-w-0 rounded-lg border border-[#dfe5ee] bg-white shadow-sm">
          <div className="border-b border-[#dfe5ee] p-4">
            <div className="flex flex-wrap gap-2">
              {tabs.map((tab) => (
                <TabButton
                  key={tab.id}
                  tab={tab}
                  activeTab={activeTab}
                  setActiveTab={setActiveTab}
                />
              ))}
            </div>
          </div>

          <div className="p-5">
            {error && (
              <div className="mb-5 rounded-lg border border-[#fecaca] bg-[#fef2f2] px-4 py-3 text-sm font-medium text-[#991b1b]">
                {error}
              </div>
            )}

            {activeTab === "chat" && (
              <WorkbenchPanel
                title="Ask Senior Engineer"
                description="Grounded answers from indexed files, symbols, and source ranges."
                actionLabel="Ask"
                isLoading={pendingAction === "ask"}
                onAction={handleAsk}
              >
                <textarea
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  className="min-h-32 w-full resize-y rounded-lg border border-[#cbd5e1] bg-[#f8fafc] p-4 text-base outline-none transition focus:border-[#0f766e] focus:ring-4 focus:ring-[#0f766e]/10"
                />

                {answer && (
                  <>
                    <MarkdownBlock content={answer} />
                    <SourcesList sources={sources} />
                  </>
                )}
              </WorkbenchPanel>
            )}

            {activeTab === "architecture" && (
              <WorkbenchPanel
                title="Architecture Analysis"
                description="System map, entry points, runtime flow, configuration, and risks."
                actionLabel="Generate Architecture"
                isLoading={pendingAction === "architecture"}
                onAction={handleArchitecture}
              >
                {architecture ? (
                  <MarkdownBlock content={architecture} />
                ) : (
                  <EmptyState text="Generate an architecture report after indexing a repository." />
                )}
              </WorkbenchPanel>
            )}

            {activeTab === "onboarding" && (
              <WorkbenchPanel
                title="Developer Onboarding Guide"
                description="First-day reading path, setup notes, mental model, and team questions."
                actionLabel="Generate Guide"
                isLoading={pendingAction === "onboarding"}
                onAction={handleOnboarding}
              >
                {onboarding ? (
                  <MarkdownBlock content={onboarding} />
                ) : (
                  <EmptyState text="Generate an onboarding guide after indexing a repository." />
                )}
              </WorkbenchPanel>
            )}
          </div>
        </section>
      </section>
    </main>
  );
}

function StatusPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[#dfe5ee] bg-[#f8fafc] px-3 py-2 text-sm">
      <span className="font-medium text-[#4b5563]">{label}</span>
      <span className="ml-2 font-semibold text-[#111827]">{value}</span>
    </div>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Activity;
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-lg border border-[#dfe5ee] bg-[#f8fafc] p-3">
      <div className="flex items-center gap-2 text-sm text-[#64748b]">
        <Icon size={16} />
        {label}
      </div>
      <p className="mt-1 break-words text-lg font-semibold text-[#111827]">
        {value}
      </p>
    </div>
  );
}

function CheckItem({ text }: { text: string }) {
  return (
    <div className="flex gap-2">
      <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-[#5eead4]" />
      <span>{text}</span>
    </div>
  );
}

function TabButton({
  tab,
  activeTab,
  setActiveTab,
}: {
  tab: { id: TabId; label: string; icon: typeof BrainCircuit };
  activeTab: TabId;
  setActiveTab: (id: TabId) => void;
}) {
  const Icon = tab.icon;
  const active = activeTab === tab.id;

  return (
    <button
      onClick={() => setActiveTab(tab.id)}
      className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition ${
        active
          ? "bg-[#0f766e] text-white"
          : "bg-[#f1f5f9] text-[#475569] hover:bg-[#e2e8f0]"
      }`}
    >
      <Icon size={17} />
      {tab.label}
    </button>
  );
}

function WorkbenchPanel({
  title,
  description,
  actionLabel,
  isLoading,
  onAction,
  children,
}: {
  title: string;
  description: string;
  actionLabel: string;
  isLoading: boolean;
  onAction: () => void;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-5 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">{title}</h2>
          <p className="mt-1 max-w-2xl text-sm text-[#64748b]">{description}</p>
        </div>
        <button
          onClick={onAction}
          disabled={isLoading}
          className="flex items-center justify-center gap-2 rounded-lg bg-[#0f766e] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#115e59] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? (
            <Loader2 size={18} className="animate-spin" />
          ) : (
            <ArrowRight size={18} />
          )}
          {actionLabel}
        </button>
      </div>
      {children}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-[#cbd5e1] bg-[#f8fafc] p-8 text-center text-sm font-medium text-[#64748b]">
      {text}
    </div>
  );
}

function SourcesList({ sources }: { sources: string[] }) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 rounded-lg border border-[#dfe5ee] bg-[#f8fafc] p-4">
      <p className="text-sm font-semibold text-[#334155]">Retrieved Sources</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {sources.slice(0, 18).map((source) => (
          <span
            key={source}
            className="rounded-lg border border-[#cbd5e1] bg-white px-3 py-1 text-sm text-[#475569]"
          >
            {source}
          </span>
        ))}
      </div>
    </div>
  );
}

function MarkdownBlock({ content }: { content: string }) {
  return (
    <div className="markdown-body mt-5 rounded-lg border border-[#dfe5ee] bg-white p-5 text-[#1f2937]">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
