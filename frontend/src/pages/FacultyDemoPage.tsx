import { Link } from 'react-router-dom'
import {
  Activity,
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  FileLock2,
  GraduationCap,
  HeartHandshake,
  LockKeyhole,
  MessageSquareText,
  Network,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
  Users,
} from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import '../styles/faculty-demo.css'

type DemoWorkflow = {
  step: string
  title: string
  description: string
}

type DemoRoutingCase = {
  request: string
  category: string
  urgency: 'Routine' | 'Moderate' | 'High' | 'Emergency'
  authority: string
}

const workflow: DemoWorkflow[] = [
  {
    step: '01',
    title: 'Student Request',
    description:
      'A student describes an issue or support request in natural language.',
  },
  {
    step: '02',
    title: 'Issue Recognition',
    description:
      'Agent 66 identifies the support category without making a clinical diagnosis.',
  },
  {
    step: '03',
    title: 'Urgency Triage',
    description:
      'The request is assessed for routine, moderate, high-alert, or emergency routing.',
  },
  {
    step: '04',
    title: 'Authority Routing',
    description:
      'The request is directed to an appropriate authorised institutional role.',
  },
  {
    step: '05',
    title: 'Human Action',
    description:
      'Authorised personnel review the request and determine the appropriate human response.',
  },
  {
    step: '06',
    title: 'Follow-up',
    description:
      'Permitted follow-up actions are tracked while sensitive records remain restricted.',
  },
]

const routingCases: DemoRoutingCase[] = [
  {
    request: 'I am struggling with one of my subjects and need academic guidance.',
    category: 'Academic / Learning Support',
    urgency: 'Routine',
    authority: 'Faculty / Mentor',
  },
  {
    request: 'My attendance record appears incorrect and I need help resolving it.',
    category: 'Attendance',
    urgency: 'Routine',
    authority: 'Faculty / Mentor',
  },
  {
    request: 'I need help understanding an issue related to my examination.',
    category: 'Examination Support',
    urgency: 'Moderate',
    authority: 'Faculty / HOD',
  },
  {
    request: 'I would like to speak privately with someone about my wellbeing.',
    category: 'Wellbeing / Counselling Request',
    urgency: 'Moderate',
    authority: 'Counsellor',
  },
  {
    request: 'I need an academic accommodation because of a private support matter.',
    category: 'Academic Accommodation',
    urgency: 'Moderate',
    authority: 'Authorised Academic Authority',
  },
  {
    request: 'I am being bullied and I do not feel safe dealing with this alone.',
    category: 'Safety / Harassment Concern',
    urgency: 'High',
    authority: 'Designated Authority / HOD',
  },
  {
    request: 'There is an immediate risk to someone’s safety.',
    category: 'Emergency / Safety',
    urgency: 'Emergency',
    authority: 'Immediate Designated Human Authority',
  },
]

const capabilities = [
  {
    icon: Network,
    title: 'Intelligent Routing',
    description:
      'Maps student support requests to appropriate authorised institutional roles.',
  },
  {
    icon: ShieldAlert,
    title: 'Crisis Escalation',
    description:
      'High-risk safety indicators bypass normal queues and trigger immediate human escalation.',
  },
  {
    icon: HeartHandshake,
    title: 'Counsellor Referral',
    description:
      'Supports referral queues, counsellor assignment, status tracking, and human follow-up.',
  },
  {
    icon: CalendarDays,
    title: 'Appointment Support',
    description:
      'Supports structured appointment scheduling between authorised users and students.',
  },
  {
    icon: FileLock2,
    title: 'Restricted Records',
    description:
      'Counselling records are treated separately from ordinary academic information.',
  },
  {
    icon: GraduationCap,
    title: 'Academic Accommodation',
    description:
      'Supports accommodation coordination without unnecessarily disclosing sensitive reasons.',
  },
  {
    icon: BookOpen,
    title: 'Resource Directory',
    description:
      'Surfaces approved wellbeing and institutional support resources.',
  },
  {
    icon: Activity,
    title: 'Aggregate Reporting',
    description:
      'Provides anonymised aggregate information for authorised leadership roles.',
  },
  {
    icon: ClipboardList,
    title: 'Audit Trail',
    description:
      'Supports accountability for protected operations and authorised system activity.',
  },
]

function urgencyClass(urgency: DemoRoutingCase['urgency']) {
  return `faculty-demo-urgency faculty-demo-urgency-${urgency.toLowerCase()}`
}

export function FacultyDemoPage() {
  const reduceMotion = useReducedMotion()

  return (
    <main className="faculty-demo-page">
      <header className="faculty-demo-header">
        <div className="faculty-demo-header-inner">
          <Link className="faculty-demo-back" to="/login">
            <ArrowLeft size={17} aria-hidden />
            Back to secure login
          </Link>

          <div className="faculty-demo-mode">
            <ShieldCheck size={17} aria-hidden />
            DEMO MODE — FOR FACULTY EVALUATION
          </div>
        </div>
      </header>

      <section className="faculty-demo-hero">
        <motion.div
          className="faculty-demo-hero-content"
          initial={reduceMotion ? false : { opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: reduceMotion ? 0 : 0.45,
            ease: [0.22, 1, 0.36, 1],
          }}
        >
          <div className="faculty-demo-brand">
            <div className="faculty-demo-brand-mark" aria-hidden>
              66
            </div>

            <div>
              <p className="faculty-demo-eyebrow">
                Counselling Support System
              </p>
              <h1>Agent 66 Faculty Evaluation</h1>
            </div>
          </div>

          <p className="faculty-demo-lead">
            A controlled demonstration of how Agent 66 recognises student
            support needs, assesses routing urgency, and connects requests
            with authorised human support.
          </p>

          <div className="faculty-demo-privacy-banner">
            <LockKeyhole size={21} aria-hidden />
            <div>
              <strong>Simulated data only</strong>
              <span>
                This demonstration does not display real student records,
                counselling records, credentials, or personally identifiable
                information.
              </span>
            </div>
          </div>

          <div className="faculty-demo-summary-grid">
            <div>
              <strong>Human-centred</strong>
              <span>AI assists recognition and routing.</span>
            </div>

            <div>
              <strong>Privacy-aware</strong>
              <span>Sensitive support records remain restricted.</span>
            </div>

            <div>
              <strong>Safety-first</strong>
              <span>Emergency concerns bypass ordinary queues.</span>
            </div>
          </div>
        </motion.div>
      </section>

      <section className="faculty-demo-section">
        <div className="faculty-demo-section-heading">
          <span>01</span>
          <div>
            <p>System Workflow</p>
            <h2>From student request to authorised human support</h2>
          </div>
        </div>

        <div className="faculty-demo-workflow">
          {workflow.map((item, index) => (
            <div className="faculty-demo-workflow-item" key={item.step}>
              <div className="faculty-demo-workflow-number">
                {item.step}
              </div>

              <div className="faculty-demo-workflow-content">
                <h3>{item.title}</h3>
                <p>{item.description}</p>
              </div>

              {index < workflow.length - 1 ? (
                <ArrowRight
                  className="faculty-demo-workflow-arrow"
                  size={20}
                  aria-hidden
                />
              ) : (
                <CheckCircle2
                  className="faculty-demo-workflow-arrow"
                  size={20}
                  aria-hidden
                />
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="faculty-demo-section faculty-demo-section-soft">
        <div className="faculty-demo-section-heading">
          <span>02</span>
          <div>
            <p>Routing Demonstration</p>
            <h2>Example student issues and authority routing</h2>
          </div>
        </div>

        <p className="faculty-demo-section-description">
          The examples below are synthetic evaluation scenarios. They
          demonstrate the intended routing behaviour without accessing
          production records or creating real referrals.
        </p>

        <div className="faculty-demo-routing-table-wrap">
          <table className="faculty-demo-routing-table">
            <thead>
              <tr>
                <th>Simulated student request</th>
                <th>Detected category</th>
                <th>Urgency</th>
                <th>Appropriate authority</th>
              </tr>
            </thead>

            <tbody>
              {routingCases.map((item) => (
                <tr key={item.request}>
                  <td>
                    <div className="faculty-demo-request">
                      <MessageSquareText size={17} aria-hidden />
                      <span>{item.request}</span>
                    </div>
                  </td>

                  <td>{item.category}</td>

                  <td>
                    <span className={urgencyClass(item.urgency)}>
                      {item.urgency}
                    </span>
                  </td>

                  <td>
                    <div className="faculty-demo-authority">
                      <UserCheck size={17} aria-hidden />
                      <span>{item.authority}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="faculty-demo-section">
        <div className="faculty-demo-section-heading">
          <span>03</span>
          <div>
            <p>Implemented Support Areas</p>
            <h2>Core Agent 66 capabilities</h2>
          </div>
        </div>

        <div className="faculty-demo-capability-grid">
          {capabilities.map(({ icon: Icon, title, description }) => (
            <article className="faculty-demo-capability-card" key={title}>
              <div className="faculty-demo-capability-icon">
                <Icon size={22} aria-hidden />
              </div>

              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="faculty-demo-section faculty-demo-safety">
        <div className="faculty-demo-safety-icon">
          <ShieldAlert size={30} aria-hidden />
        </div>

        <div>
          <p className="faculty-demo-eyebrow">Safety Boundary</p>
          <h2>Agent 66 supports routing — not counselling or diagnosis</h2>

          <p>
            The system is designed to recognise support indicators and route
            students to authorised humans. It does not replace counsellors,
            diagnose mental-health conditions, or independently provide
            emergency intervention.
          </p>

          <div className="faculty-demo-safety-flow">
            <div>
              <span>Routine</span>
              <strong>Normal authorised routing</strong>
            </div>

            <ArrowRight size={18} aria-hidden />

            <div>
              <span>Moderate</span>
              <strong>Human support prioritised</strong>
            </div>

            <ArrowRight size={18} aria-hidden />

            <div>
              <span>High Alert</span>
              <strong>Immediate human escalation</strong>
            </div>

            <ArrowRight size={18} aria-hidden />

            <div>
              <span>Emergency</span>
              <strong>Bypass normal queues</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="faculty-demo-section faculty-demo-architecture">
        <div className="faculty-demo-section-heading">
          <span>04</span>
          <div>
            <p>Privacy Architecture</p>
            <h2>Role-based and restricted information access</h2>
          </div>
        </div>

        <div className="faculty-demo-access-grid">
          <article>
            <Users size={22} aria-hidden />
            <h3>Students</h3>
            <p>
              Submit support requests and access appropriate support
              resources.
            </p>
          </article>

          <article>
            <UserCheck size={22} aria-hidden />
            <h3>Counsellors</h3>
            <p>
              Access authorised counselling referrals, appointments,
              follow-ups, and restricted records.
            </p>
          </article>

          <article>
            <GraduationCap size={22} aria-hidden />
            <h3>Academic Authorities</h3>
            <p>
              Receive only information required for authorised academic
              support and accommodations.
            </p>
          </article>

          <article>
            <LockKeyhole size={22} aria-hidden />
            <h3>Restricted Data</h3>
            <p>
              Sensitive counselling information is separated from ordinary
              academic and faculty-facing information.
            </p>
          </article>
        </div>
      </section>

      <footer className="faculty-demo-footer">
        <div>
          <div className="faculty-demo-footer-brand">
            <span>66</span>
            <strong>Agent 66</strong>
          </div>

          <p>
            Faculty Evaluation Demo — simulated information only.
          </p>
        </div>

        <div className="faculty-demo-footer-links">
          <Link to="/privacy">Privacy Policy</Link>
          <Link to="/terms">Terms of Use</Link>
          <Link to="/login">Secure Login</Link>
        </div>
      </footer>
    </main>
  )
}