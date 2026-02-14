"use client";

import type { ReviewResponse } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ConfidenceBar } from "@/components/confidence-bar";
import { AgentDetails } from "@/components/agent-details";
import { DecisionPanel } from "@/components/decision-panel";

interface ReviewDashboardProps {
  review: ReviewResponse;
}

export function ReviewDashboard({ review }: ReviewDashboardProps) {
  return (
    <div className="mt-8 space-y-6">
      {/* Recommendation header */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center gap-3">
            <CardTitle className="text-lg">Review Result</CardTitle>
            <Badge
              variant={
                review.recommendation === "approve" ? "success" : "warning"
              }
            >
              {review.recommendation === "approve"
                ? "Recommend Approve"
                : "Pend for Review"}
            </Badge>
            <Badge variant="outline">{review.confidence_level}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm font-medium mb-1">Confidence</p>
            <ConfidenceBar value={review.confidence} className="max-w-sm" />
          </div>

          <div>
            <p className="text-sm font-medium mb-1">Summary</p>
            <p className="text-sm text-muted-foreground">{review.summary}</p>
          </div>
        </CardContent>
      </Card>

      {/* Tool checks */}
      {review.tool_results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
              Verification Checks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {review.tool_results.map((t, i) => (
                <Badge
                  key={i}
                  variant={
                    t.status === "pass"
                      ? "success"
                      : t.status === "warning"
                        ? "warning"
                        : "destructive"
                  }
                >
                  {t.tool_name}: {t.detail}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Coverage criteria */}
      {(review.coverage_criteria_met.length > 0 ||
        review.coverage_criteria_not_met.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
              Coverage Criteria
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {review.coverage_criteria_met.length > 0 && (
              <div>
                <p className="text-sm font-medium text-green-700 mb-1">
                  Criteria Met
                </p>
                <ul className="list-disc list-inside text-sm text-muted-foreground space-y-0.5">
                  {review.coverage_criteria_met.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </div>
            )}
            {review.coverage_criteria_not_met.length > 0 && (
              <div>
                <p className="text-sm font-medium text-red-700 mb-1">
                  Criteria Not Met
                </p>
                <ul className="list-disc list-inside text-sm text-muted-foreground space-y-0.5">
                  {review.coverage_criteria_not_met.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Missing documentation */}
      {review.missing_documentation.length > 0 && (
        <Alert variant="destructive">
          <AlertTitle>Missing Documentation</AlertTitle>
          <AlertDescription>
            <ul className="list-disc list-inside mt-1 space-y-0.5">
              {review.missing_documentation.map((doc, i) => (
                <li key={i}>{doc}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Documentation gaps */}
      {review.documentation_gaps.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
              Documentation Gaps
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {review.documentation_gaps.map((gap, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <Badge
                  variant={gap.critical ? "destructive" : "warning"}
                  className="mt-0.5 shrink-0"
                >
                  {gap.critical ? "Critical" : "Non-critical"}
                </Badge>
                <div>
                  <p className="font-medium">{gap.what}</p>
                  <p className="text-muted-foreground">{gap.request}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Policy references */}
      {review.policy_references.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
              Policy References
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-0.5">
              {review.policy_references.map((ref, i) => (
                <li key={i}>{ref}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Clinical rationale */}
      {review.clinical_rationale && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
              Clinical Rationale
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">
              {review.clinical_rationale}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Agent details */}
      {review.agent_results && (
        <AgentDetails results={review.agent_results} />
      )}

      {/* Decision panel */}
      <DecisionPanel review={review} />

      {/* Audit trail */}
      {review.audit_trail && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
              Audit Trail
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
              <div>
                <p className="font-medium">Review Started</p>
                <p className="text-muted-foreground">
                  {review.audit_trail.review_started}
                </p>
              </div>
              <div>
                <p className="font-medium">Review Completed</p>
                <p className="text-muted-foreground">
                  {review.audit_trail.review_completed}
                </p>
              </div>
              <div>
                <p className="font-medium">Criteria Met</p>
                <p className="text-muted-foreground">
                  {review.audit_trail.criteria_met_count}
                </p>
              </div>
              <div>
                <p className="font-medium">Extraction Confidence</p>
                <ConfidenceBar
                  value={review.audit_trail.extraction_confidence}
                  className="w-32"
                />
              </div>
              <div>
                <p className="font-medium">Assessment Confidence</p>
                <ConfidenceBar
                  value={review.audit_trail.assessment_confidence}
                  className="w-32"
                />
              </div>
              {review.audit_trail.data_sources.length > 0 && (
                <div className="col-span-full">
                  <p className="font-medium mb-1">Data Sources</p>
                  <div className="flex flex-wrap gap-1">
                    {review.audit_trail.data_sources.map((src, i) => (
                      <Badge key={i} variant="outline" className="text-xs">
                        {src}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Disclaimer */}
      {review.disclaimer && (
        <>
          <Separator />
          <p className="text-xs text-muted-foreground italic px-1">
            {review.disclaimer}
          </p>
        </>
      )}
    </div>
  );
}
