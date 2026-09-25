# SC001 Current Roadmap and Stop Rules v5.80

Date: 2026-09-25  
Status: **B15-P1 HOST DEPLOYMENT READINESS PASS / REBOOT BEFORE FIRST COLLECTOR START**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.79.md`

## Host readiness result

Verified wrapper:

`scripts/research/run-b15p1-collector-host-deployment-readiness-v0.1.sh`

Wrapper SHA256:

`a962e3f1e071106228202e94af964e6c52faf1a13ca4b00c0b8ddaab6baedbdb`

Observed host result:

`B15P1_COLLECTOR_HOST_DEPLOYMENT_READINESS_PASS`

Host report SHA256:

`12268dcd0ffe5fa8af7315071640436914b71b458f513ec2a4a7d2bd148cdf4a`

## Verified actual VPS state

- collector v0.1.3 staged self-test PASS;
- freeze SHA256 = `cdc6654ce5bbf265ce5cc5af2e448806ba306292d29fb986c7eb78bb1379df96`;
- runner SHA256 = `f8181c4f25d6fc842d13c1faf8e259756883fcbb0bbcf08c23b3e60c9ed7bce0`;
- library SHA256 = `f4e27edff5acb38fb1c9ee840490179d1c3ebe13fd258d8875de768acc4078b5`;
- base assets = 146;
- overlay assets = 46;
- asset common representations = 207;
- quote common representations = 12;
- quote one-sided representations = 14;
- live snapshot contract PASS;
- live snapshot SHA256 = `14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc`;
- stable service active state = inactive;
- stable service enabled state = not-found;
- runtime stable unit = absent;
- runtime launch authorization = absent;
- collector start = false;
- systemd start/enable = false.

## OS restart hold

The terminal displayed:

`*** System restart required ***`

Before the first prospective collector start, reboot the VPS while the collector is still absent/inactive.

Reason:
- avoid introducing an immediate process-restart/source-gap into the protected prospective chronology;
- apply pending OS/kernel changes before the 7-day first operational review window begins;
- re-establish a clean host-readiness baseline after reboot.

## After reboot

Reconnect to VPS and rerun exactly:

`sudo bash /var/lib/botmarket-github-control/repo/scripts/research/run-b15p1-collector-host-deployment-readiness-v0.1.sh`

Expected again:

`B15P1_COLLECTOR_HOST_DEPLOYMENT_READINESS_PASS`

Only after a post-reboot PASS should we prepare/execute the final deployment + runtime launch authorization + collector start gate.

## Stop rule

Do not install/start/enable collector before reboot.

Do not create active runtime `collector_launch_authorization.json`.

Price/PnL research remains unauthorized.

## Next state

`AWAIT_VPS_REBOOT_BEFORE_FINAL_COLLECTOR_LAUNCH_GATE`
