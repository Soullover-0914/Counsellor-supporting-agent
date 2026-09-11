import { Link } from 'react-router-dom'

export function TermsPage() {
  return (
    <article className="policy-page">
      <header>
        <p className="privacy-chip">Institutional terms</p>
        <h1>Terms of Use</h1>
        <p className="lede">
          These terms explain the intended use of Agent 66 for{' '}
          <strong>[Institution Name]</strong>. By signing in, you agree to use the
          system responsibly and in accordance with institutional policy.
        </p>
      </header>

      <section className="policy-section">
        <h2>Intended use</h2>
        <p>
          Agent 66 is provided to help identify students who may benefit from
          professional counselling support and to route those requests to
          authorised human personnel. It is a support-routing platform, not a
          therapy service, diagnostic tool, or emergency dispatch system.
        </p>
      </section>

      <section className="policy-section">
        <h2>Account registration and approval</h2>
        <p>
          Student accounts are created only after an authorised administrator
          approves a registration request. Submitting a registration does not
          grant access. Users are responsible for protecting credentials issued
          to them and for completing the required one-time temporary password
          change.
        </p>
      </section>

      <section className="policy-section">
        <h2>Password security</h2>
        <p>
          Temporary passwords must be changed once through the designated
          workflow. After that change, the password cannot be changed again
          through the same workflow. Users must not share credentials or attempt
          to bypass authentication controls.
        </p>
      </section>

      <section className="policy-section">
        <h2>Account registration and password security</h2>
        <ul>
          <li>Student accounts require administrator approval before activation.</li>
          <li>Users are responsible for protecting sign-in credentials.</li>
          <li>
            Temporary passwords issued after approval must be changed once through
            the initial password-change workflow and cannot be changed again through
            that workflow.
          </li>
          <li>Access only information you are authorised to view.</li>
          <li>Treat counselling-related information as confidential.</li>
          <li>Follow institutional safeguarding and emergency procedures when required.</li>
        </ul>
      </section>

      <section className="policy-section">
        <h2>User responsibilities</h2>
        <ul>
          <li>Protect your sign-in credentials and sign out on shared devices.</li>
          <li>Submit accurate information relevant to support routing.</li>
          <li>Access only information you are authorised to view.</li>
          <li>Treat counselling-related information as confidential.</li>
          <li>Follow institutional safeguarding and emergency procedures when required.</li>
        </ul>
      </section>

      <section className="policy-section">
        <h2>System limitations</h2>
        <p>
          Automated triage indicators communicate support priority for human
          review. They are not clinical diagnoses. Availability of counsellors,
          appointments, and institutional resources depends on operational
          capacity outside this interface.
        </p>
      </section>

      <section className="policy-section">
        <h2>Human oversight</h2>
        <p>
          Authorised professionals remain responsible for reviewing referrals,
          managing escalations, documenting sessions, and approving academic
          accommodations. The system assists workflow; it does not replace
          professional duty of care.
        </p>
      </section>

      <section className="policy-section">
        <h2>Emergency limitations</h2>
        <p>
          If you or someone else is in immediate danger, contact local emergency
          services and institution-approved crisis channels. Agent 66 may surface
          approved contacts returned by the backend, but it cannot guarantee
          real-time emergency response.
        </p>
      </section>

      <section className="policy-section">
        <h2>Access restrictions</h2>
        <p>
          Unauthorised access, attempts to bypass role controls, misuse of
          confidential records, or interference with audit and security controls
          are prohibited and may result in account suspension and institutional
          action under applicable policies.
        </p>
      </section>

      <section className="policy-section">
        <h2>Institutional policies</h2>
        <p>
          Use of Agent 66 is also governed by institutional IT, privacy,
          safeguarding, and student-support policies maintained by{' '}
          <strong>[Institution Name]</strong>. Where those policies conflict with
          this summary page, institutional policy controls.
        </p>
      </section>

      <p className="policy-meta">
        <Link to="/login">Return to sign in</Link>
        {' · '}
        <Link to="/privacy">Privacy Policy</Link>
      </p>
    </article>
  )
}
