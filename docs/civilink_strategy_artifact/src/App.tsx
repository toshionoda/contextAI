import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import './App.css'

const SECTIONS = [
  { id: 'brief', label: 'Brief', no: '01' },
  { id: 'theory', label: 'Theory', no: '02' },
  { id: 'mechanism', label: 'Mechanism', no: '03' },
  { id: 'sales', label: 'Sales', no: '04' },
  { id: 'personas', label: 'Personas', no: '18', mark: true },
  { id: 'features', label: 'Features', no: '05' },
  { id: 'plan', label: 'Plan', no: '06' },
  { id: 'issues', label: 'Issues', no: '07' },
]

function Masthead() {
  return (
    <header className="border-b border-ink/20">
      <div className="max-w-6xl mx-auto px-6 pt-10 pb-6">
        <div className="flex items-center justify-between text-[11px] tracking-[0.2em] uppercase font-mono-tight text-foreground/60 mb-6">
          <span>CiviLink Strategic Brief</span>
          <span>Vol. 1 · No. 18 · Draft</span>
          <span className="hidden sm:block">2026 · 05 · 10</span>
        </div>
        <div className="rule-thick mb-6"></div>
        <h1 className="font-display text-[clamp(2.5rem,6vw,5rem)] font-light leading-[0.95] tracking-tight text-ink">
          死の谷を、<br />
          <span className="font-jp-serif italic font-normal">福山1社で越える。</span>
        </h1>
        <div className="mt-6 flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <p className="font-jp-serif text-lg text-foreground/80 max-w-2xl leading-relaxed">
            キャズムは「マーケティング問題」ではなく「信頼問題」。<br />
            早期多数派が買う唯一の理由は<span className="font-bold">「自分と同じ業界・同じ規模・同じ業務の会社が成果を出している」</span>。<br />
            ニッチ内浸透50%以上で初めて超える。
          </p>
          <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-foreground/50 shrink-0">
            <div>Author · Noda Toshio</div>
            <div>Source · civilink_chasm_strategy_2026-04-30.md</div>
            <div>Status · Part 18 未確定</div>
          </div>
        </div>
      </div>
      <div className="bg-ink py-3">
        <div className="max-w-6xl mx-auto px-6 flex items-center gap-4 text-paper">
          <span className="font-mono-tight text-[10px] uppercase tracking-[0.25em] opacity-70">Pin 1</span>
          <span className="w-8 h-px bg-paper/40"></span>
          <span className="font-display italic text-lg md:text-xl">福山コンサル詳細設計部門・渋谷正一さんのDocuWorks廃止宣言獲得</span>
        </div>
      </div>
    </header>
  )
}

function SectionHeader({ no, kicker, title, lede }: { no: string; kicker: string; title: string; lede?: string }) {
  return (
    <div className="mb-10">
      <div className="flex items-baseline gap-4 font-mono-tight text-[10px] uppercase tracking-[0.2em] text-foreground/50 mb-3">
        <span className="font-bold text-ink">§ {no}</span>
        <span>{kicker}</span>
      </div>
      <h2 className="font-display text-4xl md:text-5xl font-light tracking-tight text-ink leading-[1.05]">{title}</h2>
      {lede && <p className="mt-4 font-jp-serif text-base md:text-lg text-foreground/70 max-w-3xl leading-relaxed">{lede}</p>}
      <div className="rule-thin mt-6"></div>
    </div>
  )
}

function Brief() {
  const phases = [
    { phase: 'CPF', name: '課題発見', status: '達成', tone: 'common', glyph: '✓' },
    { phase: 'PSF', name: '解決策フィット', status: '非対称', tone: 'warn', glyph: '◐' },
    { phase: 'PMF', name: 'プロダクト市場フィット', status: '死の谷', tone: 'shousa', glyph: '✗' },
    { phase: 'SMF', name: 'スケール', status: '時期尚早', tone: 'shousa', glyph: '✗' },
  ]
  return (
    <div>
      <SectionHeader no="01" kicker="The Diagnosis" title="現在地：死の谷で停滞" lede="Early Adopter市場ではPSF達成（栗山・渋谷・石永）。Early Majority市場ではPSF未達（道路設計5人・三井住友16名・JFE32名）。MRR 50万・有償16社の大半は付き合い的有償化。" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {phases.map((p, i) => (
          <div key={p.phase} className="border border-ink/15 p-5 bg-card relative">
            <div className="absolute top-0 left-0 px-2 py-0.5 bg-ink text-paper font-mono-tight text-[10px] tracking-widest">
              {String(i + 1).padStart(2, '0')}
            </div>
            <div className="font-display text-3xl mt-3 mb-1">{p.phase}</div>
            <div className="text-xs text-foreground/60 mb-4">{p.name}</div>
            <div className={`inline-flex items-center gap-1.5 text-${p.tone} font-mono-tight text-[11px] uppercase tracking-wider`}>
              <span className="text-base">{p.glyph}</span>
              {p.status}
            </div>
          </div>
        ))}
      </div>

      <div className="bg-shousa-bg border-l-4 border-shousa p-6 md:p-8">
        <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-shousa font-bold mb-2">Root Bottleneck</div>
        <p className="font-jp-serif text-xl md:text-2xl leading-snug text-ink">
          有償16社いるのに、<span className="font-bold">DocuWorks廃止宣言</span>を獲得した顧客は<span className="text-shousa">事実上ゼロ</span>。<br />
          ワークフロー乗っ取りを完遂した参照事例がない。
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mt-8">
        <div className="border border-ink/15 p-6">
          <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-foreground/50 mb-3">死の谷で詰まる典型パターン</div>
          <ul className="space-y-2 text-sm">
            {[
              'VoCを聞きすぎて機能が肥大化',
              'トライアル提供を続けるがCVR上がらない',
              '「コンセプトは良い」「あったら便利」止まり',
              'Early Adopter偏重でEarly Majorityと乖離',
              'ペルソナを絞り込めず全方位で薄く戦う',
              'Aha! Momentが再現性ない',
              'Loss Interviewを実施していない',
            ].map((t) => (
              <li key={t} className="flex gap-2 leading-relaxed">
                <span className="text-shousa mt-0.5">✓</span>
                <span>{t}</span>
              </li>
            ))}
          </ul>
          <p className="text-xs text-foreground/60 mt-3 italic">→ ほぼフルセットで該当。</p>
        </div>
        <div className="border border-ink/15 p-6 bg-paper">
          <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-foreground/50 mb-3">解決の優先順位</div>
          <ol className="space-y-3 text-sm">
            {[
              { rank: '🥇', title: '有償化→定着（[C]＝乗っ取り完遂）', detail: 'レバー最大、なくては他が動かない' },
              { rank: '🥈', title: '営業戦略（3社集中・KPI再設計）', detail: '[C]の成功確率を上げる前提条件' },
              { rank: '🥉', title: 'デモ → 業務診断セッション', detail: '戦術レベル、[C]成功後に最速で効く' },
              { rank: '○', title: 'キャズム越え', detail: '12-24ヶ月先、今手をつける段階ではない' },
            ].map((o) => (
              <li key={o.title} className="flex gap-3 pb-3 border-b border-ink/10 last:border-0">
                <span className="font-mono-tight text-base">{o.rank}</span>
                <div>
                  <div className="font-bold text-ink">{o.title}</div>
                  <div className="text-xs text-foreground/60 mt-0.5">{o.detail}</div>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  )
}

function Theory() {
  return (
    <div>
      <SectionHeader no="02" kicker="Chasm Theory" title="買う理由は、ただ一つ" />

      <blockquote className="font-display text-3xl md:text-4xl italic font-light text-ink leading-snug border-l-4 border-shousa pl-6 md:pl-10 my-10 max-w-4xl">
        早期多数派が買う唯一の理由は<br />
        <span className="not-italic font-normal font-jp-serif text-foreground/95">「自分と同じ業界・同じ規模・同じ業務の会社が、成果を出している」</span>
      </blockquote>

      <p className="font-jp-serif text-foreground/70 mb-12 max-w-3xl leading-relaxed">
        機能・価格・数字・VoC・ROI試算は全部副次的。これ以外はノイズ。<br />
        <span className="text-ink font-bold">ニッチ内浸透50%以上</span>で初めてキャズムを超える。
      </p>

      <div className="grid md:grid-cols-2 gap-0 border border-ink/20">
        <div className="p-8 border-b md:border-b-0 md:border-r border-ink/20">
          <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-foreground/50 mb-2">Type A · 既達</div>
          <h3 className="font-display text-2xl mb-1">Vision MVP</h3>
          <p className="text-sm text-foreground/60 mb-6 italic">栗山さん的なイノベーター</p>
          <dl className="space-y-3 text-sm">
            <div><dt className="text-foreground/50 text-xs">買う理由</dt><dd className="font-bold">業界の未来を見ているから</dd></div>
            <div><dt className="text-foreground/50 text-xs">最低条件</dt><dd>コア差別化機能＋ビジョン</dd></div>
            <div><dt className="text-foreground/50 text-xs">不完全さへの態度</dt><dd>「面白い、これから良くなる」</dd></div>
            <div><dt className="text-foreground/50 text-xs">必要な周辺</dt><dd>少ない</dd></div>
          </dl>
        </div>
        <div className="p-8 bg-shousa-bg/50">
          <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-shousa font-bold mb-2">Type B · 未達</div>
          <h3 className="font-display text-2xl mb-1">Whole Product MVP</h3>
          <p className="text-sm text-foreground/60 mb-6 italic">渋谷さん的な現場担当者</p>
          <dl className="space-y-3 text-sm">
            <div><dt className="text-foreground/50 text-xs">買う理由</dt><dd className="font-bold">月曜日の業務が回るから</dd></div>
            <div><dt className="text-foreground/50 text-xs">最低条件</dt><dd className="text-shousa font-bold">業務の100%代替</dd></div>
            <div><dt className="text-foreground/50 text-xs">不完全さへの態度</dt><dd>「未完成」＝拒絶</dd></div>
            <div><dt className="text-foreground/50 text-xs">必要な周辺</dt><dd>膨大（教育・移行・サポート・連携）</dd></div>
          </dl>
        </div>
      </div>

      <div className="mt-10 bg-ink text-paper p-8 md:p-10 relative overflow-hidden">
        <div className="dot-grid absolute inset-0 opacity-30"></div>
        <div className="relative">
          <div className="font-mono-tight text-[10px] uppercase tracking-[0.25em] text-paper/60 mb-3">"目が死んだ" 現象</div>
          <p className="font-jp-serif text-2xl md:text-3xl leading-snug">
            Vision MVPは栗山さんに刺さったが、<br />
            Whole Product MVPが未成立で <span className="font-display italic">5人の道路設計者には「未完成」</span> に見えた。
          </p>
        </div>
      </div>
    </div>
  )
}

function Mechanism() {
  const stages = [
    { num: '01', target: '個人ヘビー化', who: '渋谷＋照査対象設計者 5–10人', decision: 'DocuWorks廃止宣言', actor: '渋谷さん', active: true },
    { num: '02', target: '部門標準化', who: '道路設計部門 30–50人', decision: '部門標準宣言', actor: '部門長', active: false },
    { num: '03', target: '全社展開', who: '橋梁・河川・地盤の照査部門', decision: '全社標準宣言', actor: '役員', active: false },
  ]
  return (
    <div>
      <SectionHeader
        no="03"
        kicker="Takeover Mechanism"
        title="ANDPADモデル"
        lede="ライセンス販売の積み上げで広がるSaaSはほぼない。実際に広がるのは「業務上、CiviLinkを開かないと仕事が回らない人」が増える構造。各段の遷移は人数でなく、決定で起きる。"
      />

      <div className="space-y-3">
        {stages.map((s, i) => (
          <div key={s.num} className={`relative grid grid-cols-12 gap-4 border ${s.active ? 'border-shousa bg-shousa-bg' : 'border-ink/15'} p-5 md:p-6`}>
            <div className="col-span-2 md:col-span-1 flex items-start">
              <div className={`w-12 h-12 flex items-center justify-center font-display text-lg ${s.active ? 'bg-shousa text-paper pulse-ring' : 'bg-ink text-paper'}`}>
                {s.num}
              </div>
            </div>
            <div className="col-span-10 md:col-span-4">
              <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-foreground/50 mb-1">Stage {i + 1}</div>
              <div className="font-display text-2xl">{s.target}</div>
              <div className="text-sm text-foreground/60 mt-1">{s.who}</div>
            </div>
            <div className="col-span-12 md:col-span-7 md:border-l border-ink/10 md:pl-6 pt-4 md:pt-0">
              <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-foreground/50 mb-1">Trigger Decision</div>
              <div className="font-jp-serif text-lg leading-snug">「{s.decision}」</div>
              <div className="text-xs text-foreground/60 mt-2">By <span className="font-bold">{s.actor}</span></div>
            </div>
            {i < stages.length - 1 && (
              <div className="absolute -bottom-3 left-12 md:left-12 font-mono-tight text-foreground/30 text-xl">↓</div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function Sales() {
  const stages = [
    { tag: 'Stage 01', title: '業務診断セッション', price: '半日〜1日 / 対面', detail: 'ワークフロー観察＋仮説提示。売り込み禁止。デモアカウント24-48hその場発行・期限後消滅。' },
    { tag: 'Stage 02', title: '有償プロトタイプ', price: '¥1.5M – ¥3M / 2-3ヶ月', detail: '5-10人チームでワークフロー乗っ取り完遂。CS週次伴走＋効果測定＋稟議用レポート納品。' },
    { tag: 'Stage 03', title: '年契約', price: '¥6M – ¥30M / 3年', detail: '部門標準導入・部門長スポンサー。プロトタイプで廃止宣言が取れた場合のみ。' },
  ]
  const drops = [
    '訪問先で「トライアルしてみませんか」を口にしない',
    '全国デモ行脚をやめる',
    '「興味あり」「前向き」「コンセプト評価高い」をパイプラインから排除',
  ]
  return (
    <div>
      <SectionHeader
        no="04"
        kicker="Sales Re-Architecture"
        title="無料トライアルを捨てる"
        lede="無料トライアルが機能する4条件をCiviLinkは1つも満たしていない。モデルそのものを捨てる。"
      />

      <div className="grid md:grid-cols-3 gap-0 border border-ink/20 mb-8">
        {stages.map((s, i) => (
          <div key={s.tag} className={`p-6 ${i < 2 ? 'md:border-r border-ink/15' : ''} ${i > 0 ? 'border-t md:border-t-0 border-ink/15' : ''}`}>
            <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-shousa font-bold">{s.tag}</div>
            <h3 className="font-display text-xl mt-2 mb-2">{s.title}</h3>
            <div className="font-mono-tight text-sm text-ink mb-3 tabular">{s.price}</div>
            <p className="text-sm text-foreground/70 leading-relaxed">{s.detail}</p>
          </div>
        ))}
      </div>

      <div className="bg-paper border border-ink/20 p-6 md:p-8">
        <div className="flex items-baseline gap-3 mb-4">
          <span className="font-display text-3xl text-shousa">¥</span>
          <p className="font-jp-serif text-lg leading-snug text-ink">
            <span className="font-bold">故意に高くする</span>のが戦略。月5万「付き合いで」は通るが、月100万「成果出さないと社内ヤバい」は<span className="text-shousa font-bold">真剣度のフィルター</span>になる。
          </p>
        </div>
      </div>

      <div className="mt-8 grid md:grid-cols-[200px_1fr] gap-6 items-start">
        <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-foreground/50 pt-2">やめる3つ</div>
        <div className="space-y-2">
          {drops.map((d) => (
            <div key={d} className="flex gap-3 items-start">
              <span className="font-mono-tight text-shousa text-base shrink-0 mt-0.5">×</span>
              <span className="text-sm leading-relaxed">{d}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Personas() {
  const [route, setRoute] = useState<'r1' | 'r2' | 'r3'>('r2')
  const routes = {
    r1: { label: '経路1', title: '照査ピンの配下ユーザー', verdict: '既存戦略内', detail: '渋谷さん廃止宣言→部下若手5-10人が必須化。新ペルソナ不要。' },
    r2: { label: '経路2', title: '若手ニッチ商品化', verdict: '却下', detail: '新人研修・OJT補完。「現在の機能では価値が出ない」=Whole Product未成立。' },
    r3: { label: '経路3', title: 'ボトムアップ突破', verdict: '罠', detail: '若手→上司を巻き込む。建設業界（年功序列）では弱い。' },
  } as const

  return (
    <div>
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-4">
          <Badge className="bg-warn text-paper hover:bg-warn font-mono-tight text-[10px] tracking-widest rounded-none">⚠ DRAFT · 未確定</Badge>
          <span className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-foreground/50">Part 18 · 2026-05-09〜10討議</span>
        </div>
        <div className="flex items-baseline gap-4 font-mono-tight text-[10px] uppercase tracking-[0.2em] text-foreground/50 mb-3">
          <span className="font-bold text-ink">§ 18</span>
          <span>The Persona Question</span>
        </div>
        <h2 className="font-display text-4xl md:text-5xl font-light tracking-tight text-ink leading-[1.05]">
          営業マン複数。<br />
          ペルソナ、複数？
        </h2>
        <p className="mt-4 font-jp-serif text-base md:text-lg text-foreground/70 max-w-3xl leading-relaxed">
          「営業マン複数いるので、ペルソナと戦略を複数作りたい」（野田さん）。
          検討の結果、両建ては却下し、<span className="font-bold text-ink">集中継続＋若手は直列温存</span>に着地。
        </p>
        <div className="rule-thin mt-6"></div>
      </div>

      {/* 3 routes */}
      <div className="mb-12">
        <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-foreground/50 mb-4">3 Routes Considered → All Rejected</div>
        <div className="grid md:grid-cols-3 gap-3">
          {(['r1', 'r2', 'r3'] as const).map((k) => {
            const r = routes[k]
            const active = route === k
            return (
              <button
                key={k}
                onClick={() => setRoute(k)}
                className={`text-left border-2 p-5 transition-colors ${
                  active ? 'border-ink bg-ink text-paper' : 'border-ink/15 bg-card hover:border-ink/40'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className={`font-mono-tight text-[10px] uppercase tracking-widest ${active ? 'text-paper/60' : 'text-foreground/50'}`}>{r.label}</span>
                  <span className={`font-mono-tight text-[10px] tracking-widest px-2 py-0.5 ${active ? 'bg-paper text-ink' : 'bg-ink text-paper'}`}>{r.verdict}</span>
                </div>
                <div className={`font-display text-lg ${active ? 'text-paper' : 'text-ink'}`}>{r.title}</div>
                <div className={`text-xs mt-2 leading-relaxed ${active ? 'text-paper/80' : 'text-foreground/60'}`}>{r.detail}</div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Persona pivot discovery */}
      <div className="mb-12 bg-wakate-bg border border-wakate p-6 md:p-8">
        <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-wakate font-bold mb-3">The Pivotal Discovery</div>
        <p className="font-jp-serif text-xl md:text-2xl leading-snug text-ink mb-4">
          若手の業務の核は「OJT」ではなく
          <span className="font-display italic text-wakate"> 外注管理</span>
          だった。
        </p>
        <blockquote className="font-jp-serif text-base text-foreground/75 italic border-l-2 border-wakate pl-4">
          「協力会社への指示や、修正されてきた図面をすぐに確認するときに、即時価値化するもの」<br />
          <span className="text-xs not-italic text-foreground/55">— 野田さん</span>
        </blockquote>
      </div>

      {/* Persona compare */}
      <div className="grid md:grid-cols-2 gap-6 mb-12">
        <PersonaCard
          tone="shousa"
          tag="既定義"
          name="照査技術者"
          rep="渋谷正一さん"
          repDetail="福山北九州 · Issue週92回"
          rows={[
            ['業務の核', '1人で照査・過去案件参照頻繁・DW派'],
            ['Whole Product', 'DocuWorks 100%代替'],
            ['廃止宣言', '「DocuWorks廃止宣言」'],
            ['Buyer', '部門長・役員'],
            ['突破経路', 'トップダウン乗っ取り（権威）'],
            ['訴求', '履歴参照・協議透明化・見落とし防止'],
          ]}
        />
        <PersonaCard
          tone="wakate"
          tag="新規（直列温存）"
          name="若手技術者"
          rep="外注管理ハブ型"
          repDetail="社内若手 / 対外発注者"
          rows={[
            ['業務の核', '協力会社への指示・修正図面の即時確認'],
            ['Whole Product', '外注管理ワークフロー乗っ取り'],
            ['廃止宣言', '「外注成果物確認をCL標準化」'],
            ['Buyer', '部長・課長（外注管理責任者）'],
            ['突破経路', '社外（協力会社）波及エンジン'],
            ['価値検証', '即時価値化（1回目で体感）必須'],
          ]}
        />
      </div>

      {/* External diffusion */}
      <div className="mb-12 grid md:grid-cols-[1fr_2fr] gap-6 items-start border border-ink/15 p-6 md:p-8">
        <div>
          <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-foreground/50 mb-2">Strategic Implication</div>
          <h3 className="font-display text-2xl">社外波及エンジン</h3>
        </div>
        <div className="font-jp-serif text-base leading-relaxed text-foreground/85">
          「若手が外注先に出すフォーマット = CL」と決まれば、協力会社も触らざるを得ない。
          協力会社は複数の発注元を持つ → <span className="font-bold text-ink">他建設コンサルへ自然伝播</span>。
          照査線（社内乗っ取り）にない<span className="text-wakate font-bold">横展開エンジン</span>になり得る。
        </div>
      </div>

      {/* Final decision */}
      <div className="bg-ink text-paper p-8 md:p-12 relative overflow-hidden">
        <div className="dot-grid absolute inset-0 opacity-20"></div>
        <div className="relative">
          <div className="font-mono-tight text-[10px] uppercase tracking-[0.25em] text-paper/60 mb-2">Final Verdict</div>
          <h3 className="font-display text-3xl md:text-4xl mb-8 leading-tight">
            両建て却下、<span className="italic">集中継続＋直列温存</span>
          </h3>
          <div className="space-y-5 max-w-3xl">
            {[
              { n: '01', tone: 'shousa', title: 'Pin 1（照査線）に全員集中', d: '「全員=同じ仕事」ではなく「全員=Pin 1突破への役割分担」で営業マン複数を活かす。' },
              { n: '02', tone: 'wakate', title: '若手ペルソナは直列温存（Pin 2武器）', d: '捨てない・今やらない。Pin 1突破後に第2段武器として起動。' },
              { n: '03', tone: 'common', title: '機能は1系統で両線カバー', d: 'WP MVPを「DW代替」から「図面ワークフロー乗っ取り」に再定義。差分検出・トラッキングはPin 1ロードマップに統合。' },
            ].map((d) => (
              <div key={d.n} className="grid grid-cols-[40px_1fr] gap-4 items-start border-t border-paper/15 pt-5 first:border-t-0 first:pt-0">
                <div className={`text-${d.tone} font-display text-3xl leading-none`}>{d.n}</div>
                <div>
                  <div className="font-bold text-paper">{d.title}</div>
                  <div className="text-sm text-paper/70 mt-1 leading-relaxed">{d.d}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 bg-shousa-bg border-l-4 border-shousa p-5 flex gap-4 items-start">
        <span className="font-display text-2xl text-shousa">!</span>
        <p className="font-jp-serif text-base leading-snug text-ink">
          <span className="font-bold">4ヶ月放置リスクの再演を避ける。</span>
          2025-12-15の問題提起が未実行のまま4ヶ月経過。両建ては「やめる3つ＝コンセプト共感案件追跡」と同じ罠。
        </p>
      </div>
    </div>
  )
}

function PersonaCard({
  tone,
  tag,
  name,
  rep,
  repDetail,
  rows,
}: {
  tone: 'shousa' | 'wakate'
  tag: string
  name: string
  rep: string
  repDetail: string
  rows: [string, string][]
}) {
  const borderClass = tone === 'shousa' ? 'border-shousa' : 'border-wakate'
  const bgClass = tone === 'shousa' ? 'bg-shousa-bg' : 'bg-wakate-bg'
  const textClass = tone === 'shousa' ? 'text-shousa' : 'text-wakate'
  return (
    <div className={`border-2 ${borderClass}`}>
      <div className={`${bgClass} px-6 py-4 border-b-2 ${borderClass}`}>
        <div className={`${textClass} font-mono-tight text-[10px] uppercase tracking-[0.2em] font-bold`}>{tag}</div>
        <h3 className="font-display text-2xl mt-1">{name}</h3>
        <p className="text-sm text-foreground/65 mt-1">{rep} <span className="opacity-60">· {repDetail}</span></p>
      </div>
      <dl className="divide-y divide-ink/10">
        {rows.map(([k, v]) => (
          <div key={k} className="grid grid-cols-[100px_1fr] px-6 py-3 text-sm">
            <dt className="text-foreground/50 text-xs pt-0.5">{k}</dt>
            <dd className="leading-relaxed">{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

function Features() {
  const [highlight, setHighlight] = useState<'all' | 'now' | 'priority' | 'later'>('all')
  const features = [
    { name: '差分検出（Before/After）', shousa: '◎ 修正版確認', wakate: '◎ 外注成果物確認', timing: 'priority', label: '今すぐ・Pin 1統合' },
    { name: '指摘・コメント', shousa: '◎ 指摘出し', wakate: '◎ 指示出し', timing: 'now', label: '今すぐ・既存' },
    { name: '履歴・トラッキング', shousa: '◎ 協議透明化', wakate: '◎ 指示反映確認', timing: 'priority', label: '今すぐ・Pin 1統合' },
    { name: '過去案件横断検索', shousa: '◎', wakate: '△', timing: 'now', label: 'Pin 1優先' },
    { name: 'ゲストアクセス（協力会社UI）', shousa: '△', wakate: '◎', timing: 'later', label: '第2段で実装' },
  ]
  const filters: { key: typeof highlight; label: string }[] = [
    { key: 'all', label: 'All' },
    { key: 'priority', label: 'Pin 1 統合' },
    { key: 'now', label: '今すぐ' },
    { key: 'later', label: '第2段' },
  ]
  return (
    <div>
      <SectionHeader
        no="05"
        kicker="Feature Prioritization"
        title="共通か、専用か"
        lede="外注管理3機能を共通機能と専用機能に切り分け。共通機能はPin 1ロードマップに統合、専用機能はPin 1突破後。"
      />

      <div className="flex flex-wrap gap-2 mb-6 font-mono-tight text-[11px] uppercase tracking-wider">
        <span className="text-foreground/50 mr-2 self-center">filter:</span>
        {filters.map((f) => (
          <button
            key={f.key}
            onClick={() => setHighlight(f.key)}
            className={`px-3 py-1.5 border transition-colors ${
              highlight === f.key ? 'bg-ink text-paper border-ink' : 'border-ink/20 hover:border-ink/50'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="border border-ink/20 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-paper border-b border-ink/15">
            <tr className="font-mono-tight text-[10px] uppercase tracking-[0.15em] text-foreground/60">
              <th className="text-left px-5 py-3 font-semibold">機能</th>
              <th className="text-left px-5 py-3 font-semibold border-l border-ink/10">照査線</th>
              <th className="text-left px-5 py-3 font-semibold border-l border-ink/10">若手線</th>
              <th className="text-left px-5 py-3 font-semibold border-l border-ink/10">着手</th>
            </tr>
          </thead>
          <tbody>
            {features.map((f) => {
              const dim = highlight !== 'all' && highlight !== f.timing
              return (
                <tr key={f.name} className={`border-b border-ink/10 last:border-0 transition-opacity ${dim ? 'opacity-25' : ''}`}>
                  <td className="px-5 py-4 font-bold">{f.name}</td>
                  <td className="px-5 py-4 border-l border-ink/10 text-shousa font-mono-tight text-xs">{f.shousa}</td>
                  <td className="px-5 py-4 border-l border-ink/10 text-wakate font-mono-tight text-xs">{f.wakate}</td>
                  <td className="px-5 py-4 border-l border-ink/10">
                    <TimingBadge timing={f.timing} label={f.label} />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function TimingBadge({ timing, label }: { timing: string; label: string }) {
  const map: Record<string, string> = {
    priority: 'bg-shousa text-paper',
    now: 'bg-common text-paper',
    later: 'bg-foreground/40 text-paper',
  }
  return (
    <span className={`inline-block px-2 py-1 font-mono-tight text-[10px] uppercase tracking-wider ${map[timing] || 'bg-ink text-paper'}`}>
      {label}
    </span>
  )
}

function Plan() {
  const months = [
    { tag: 'M1', range: '5/7 - 6/5', title: '基盤構築', detail: '福山詳細設計部の組織図完成 · 渋谷さん週1チャンピオン会議 · 差分検出機能要件確定 · Loss Interview 5社', current: true },
    { tag: 'M2', range: '6/5 - 7/3', title: '不足解消＋実装', detail: 'Whole Product不足リスト確定 · 差分検出実装 · 稟議用レポートドラフト · 土師さん福山専属化', current: false },
    { tag: 'M3', range: '7/3 - 7/29', title: '★ 有償プロトタイプ¥3M締結', detail: '渋谷さん「DocuWorks廃止宣言」獲得 · 稟議用レポート納品 · 部門長スポンサー化', current: false, milestone: true },
    { tag: 'M4+', range: '8月以降', title: '第2段：若手ペルソナ起動', detail: '廃止宣言獲得後、外注管理専用機能（指示作成・ゲストアクセス）開発開始 → Pin 2テンプレート化', current: false, future: true },
  ]
  return (
    <div>
      <SectionHeader
        no="06"
        kicker="90-Day Plan"
        title="3ヶ月で1社、有償プロトタイプ"
        lede="最終ゴール：1社で有償プロトタイプ締結。MRR 50→100は「福山で200万PoC」で実現。"
      />

      <div className="relative">
        <div className="absolute left-[19px] top-2 bottom-2 w-px bg-ink/20"></div>
        <div className="space-y-6">
          {months.map((m) => (
            <div key={m.tag} className="relative pl-16">
              <div className={`absolute left-0 top-1 w-10 h-10 flex items-center justify-center font-mono-tight text-[11px] tracking-wider font-bold ${
                m.milestone ? 'bg-shousa text-paper pulse-ring' : m.current ? 'bg-ink text-paper' : m.future ? 'bg-paper border border-ink text-ink' : 'bg-ink/30 text-paper'
              }`}>
                {m.tag}
              </div>
              <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-foreground/50 mb-1">{m.range}</div>
              <h3 className={`font-display text-xl md:text-2xl mb-2 ${m.milestone ? 'text-shousa' : ''}`}>{m.title}</h3>
              <p className="text-sm text-foreground/70 leading-relaxed">{m.detail}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Issues() {
  const todo = [
    '戦略書v1.2として正式採用するか（経営層・川端さんとの合意必要）',
    '営業A/B/Cの具体的な担当アサイン',
    '共通機能（差分検出・トラッキング）の実装優先順位（既存実装状況の確認必要）',
    '若手線ピン1候補の特定（Pin 1突破後に再検討）',
    'ゲストアクセス機能の既存仕様確認',
  ]
  const urgent = [
    '西日本DCO早急コンタクト（4/23から放置）',
    '福山4/30満了の更新フォロー',
    '4/22 Tasuku Takatori → 野田 Slack対応',
    'Bug Bash 6件のステータス確認',
  ]
  const week = [
    '戦略書を経営層（川端さん）と合意',
    '営業×FDE推進チーム認識ズレ解消',
    'JFE石永さん追加対話（第2チャンピオン候補化）',
    '価格モデル再設計議題化',
  ]
  return (
    <div>
      <SectionHeader no="07" kicker="Open Issues" title="まだ確定していない" />

      <Card className="rounded-none border-warn border-2 mb-8 bg-paper">
        <CardContent className="p-6">
          <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-warn font-bold mb-3">Pending Confirmation · Part 18</div>
          <ul className="space-y-2 text-sm">
            {todo.map((t) => (
              <li key={t} className="flex gap-3 items-start">
                <span className="font-mono-tight text-warn shrink-0 mt-0.5">□</span>
                <span className="leading-relaxed">{t}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-4">
        <Card className="rounded-none bg-shousa-bg border-shousa">
          <CardContent className="p-6">
            <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-shousa font-bold mb-3">🚨 即日対応</div>
            <ul className="space-y-2 text-sm">
              {urgent.map((t) => (
                <li key={t} className="flex gap-2 items-start">
                  <span className="text-shousa mt-0.5">○</span>
                  <span className="leading-relaxed">{t}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
        <Card className="rounded-none bg-wakate-bg border-wakate">
          <CardContent className="p-6">
            <div className="font-mono-tight text-[10px] uppercase tracking-[0.2em] text-wakate font-bold mb-3">🥇 5月初週</div>
            <ul className="space-y-2 text-sm">
              {week.map((t) => (
                <li key={t} className="flex gap-2 items-start">
                  <span className="text-wakate mt-0.5">○</span>
                  <span className="leading-relaxed">{t}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      <Separator className="my-12 bg-ink/15" />
      <div className="text-center font-mono-tight text-[10px] uppercase tracking-[0.3em] text-foreground/40">
        — End of Brief —
      </div>
      <div className="text-center text-xs text-foreground/40 mt-3 font-jp-serif">
        Source: <code>docs/civilink_chasm_strategy_2026-04-30.md</code> · v1.1 + Part 18 (未確定)
      </div>
    </div>
  )
}

function App() {
  const [active, setActive] = useState('brief')
  const RENDER: Record<string, JSX.Element> = {
    brief: <Brief />,
    theory: <Theory />,
    mechanism: <Mechanism />,
    sales: <Sales />,
    personas: <Personas />,
    features: <Features />,
    plan: <Plan />,
    issues: <Issues />,
  }
  return (
    <div className="min-h-screen bg-background">
      <Masthead />
      <Tabs value={active} onValueChange={setActive} className="max-w-6xl mx-auto px-6 py-8">
        <TabsList className="bg-transparent p-0 h-auto w-full overflow-x-auto justify-start gap-0 border-b border-ink/15 rounded-none mb-10">
          {SECTIONS.map((s) => (
            <TabsTrigger
              key={s.id}
              value={s.id}
              className="rounded-none data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:text-ink data-[state=active]:border-ink border-b-2 border-transparent text-foreground/50 hover:text-ink px-4 py-3 transition-colors group relative"
            >
              <div className="flex items-baseline gap-2">
                <span className="font-mono-tight text-[10px] tracking-widest opacity-60">§{s.no}</span>
                <span className="font-jp-serif text-sm">{s.label}</span>
                {s.mark && (
                  <span className="ml-1 w-1.5 h-1.5 rounded-full bg-warn"></span>
                )}
              </div>
            </TabsTrigger>
          ))}
        </TabsList>
        {SECTIONS.map((s) => (
          <TabsContent key={s.id} value={s.id} className="mt-0">
            {RENDER[s.id]}
          </TabsContent>
        ))}
      </Tabs>
      <footer className="border-t border-ink/15 mt-20">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between font-mono-tight text-[10px] uppercase tracking-[0.2em] text-foreground/50">
          <span>CiviLink Strategic Brief · 2026-05-10</span>
          <span>Confidential · Internal Draft</span>
        </div>
      </footer>
    </div>
  )
}

export default App
