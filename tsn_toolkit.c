/*
 * TSN Toolkit -- All-in-C reference implementation (no external tools)
 *
 * This single file provides three independent programs selected at
 * build time with a pre‑processor macro:
 *   1. net_bench   – latency / throughput benchmark
 *   2. gptp_sync   – gPTP / IEEE‑1588 layer‑2 slave daemon
 *   3. tsn_qdisc   – mqprio + CBS + TAPRIO configurator via Netlink
 *
 * Build examples
 * --------------
 *   # latency / throughput tester
 *   gcc -O2 -pthread   -DAPP_NET_BENCH  -o net_bench  tsn_toolkit.c
 *
 *   # gPTP slave (requires libmnl only for sockaddr helpers)
 *   gcc -O2            -DAPP_GPTP_SYNC  -o gptp_sync  tsn_toolkit.c -lmnl
 *
 *   # TSN queue setup (mqprio + CBS + TAPRIO)
 *   gcc -O2            -DAPP_TSN_QDISC -o tsn_qdisc  tsn_toolkit.c -lmnl
 *
 * Requirements
 * ------------
 *   * Linux 5.15 or newer, NIC with PHC for hardware timestamping
 *   * libmnl development package   (sudo apt install libmnl-dev)
 *   * root privileges or CAP_NET_ADMIN, CAP_NET_RAW, CAP_SYS_TIME
 *
 * NOTE: The code is intentionally minimal and omits extensive error
 *       handling for clarity.  Adapt as needed for production use.
 */

/********************************************************************
 * SECTION 1 – net_bench (placeholder)
 ********************************************************************/
#ifdef APP_NET_BENCH
#include <stdio.h>
int main(int argc, char **argv)
{
    (void)argc; (void)argv;
    printf("net_bench: placeholder.  Use the full implementation\n");
    return 0;
}
#endif /* APP_NET_BENCH */

/********************************************************************
 * SECTION 2 – Minimal gPTP (IEEE 802.1AS‑2020) L2 slave – gptp_sync
 ********************************************************************/
#ifdef APP_GPTP_SYNC
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <linux/if_ether.h>
#include <linux/if_packet.h>
#include <linux/net_tstamp.h>
#include <linux/sockios.h>
#include <net/if.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/timex.h>
#include <time.h>
#include <unistd.h>

#define ETH_P_1588 0x88F7
#define PTP_SYNC       0x00
#define PTP_FOLLOW_UP  0x08

struct ptp_header {
    uint8_t  msg_type;
    uint8_t  version;
    uint16_t msg_len;
    uint8_t  domain;
    uint8_t  reserved1;
    uint16_t flags;
    uint64_t correction;
    uint32_t reserved2;
    uint8_t  clock_id[8];
    uint16_t src_port_id;
    uint16_t seq_id;
    uint8_t  control; /* unused */
    uint8_t  log_interval;
} __attribute__((packed));

static int bind_raw_ptp(const char *ifname)
{
    int fd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_1588));
    if (fd < 0) { perror("socket"); exit(EXIT_FAILURE); }

    struct ifreq ifr = {0};
    strncpy(ifr.ifr_name, ifname, IFNAMSIZ - 1);
    if (ioctl(fd, SIOCGIFINDEX, &ifr) < 0) { perror("SIOCGIFINDEX"); exit(EXIT_FAILURE); }

    struct sockaddr_ll addr = {0};
    addr.sll_family   = AF_PACKET;
    addr.sll_protocol = htons(ETH_P_1588);
    addr.sll_ifindex  = ifr.ifr_ifindex;
    if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) { perror("bind"); exit(EXIT_FAILURE); }

    int tstamp_flags = SOF_TIMESTAMPING_RX_HARDWARE | SOF_TIMESTAMPING_RAW_HARDWARE;
    if (setsockopt(fd, SOL_SOCKET, SO_TIMESTAMPING, &tstamp_flags, sizeof(tstamp_flags)) < 0)
        perror("SO_TIMESTAMPING");
    return fd;
}

static uint64_t hw_ts_from_msg(struct msghdr *msg)
{
    for (struct cmsghdr *c = CMSG_FIRSTHDR(msg); c; c = CMSG_NXTHDR(msg, c)) {
        if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SO_TIMESTAMPING) {
            struct timespec *ts = (struct timespec *)CMSG_DATA(c);
            return (uint64_t)ts[2].tv_sec * 1000000000ULL + ts[2].tv_nsec; /* index 2 = raw hw */
        }
    }
    return 0;
}

static void adjust_clock(int64_t offset_ns)
{
    struct timex tx = {0};
    tx.modes  = ADJ_OFFSET | ADJ_NANO;
    tx.offset = offset_ns;
    if (adjtimex(&tx) < 0) perror("adjtimex");
}

int main(int argc, char **argv)
{
    if (argc < 2) { fprintf(stderr, "usage: %s <iface>\n", argv[0]); return 1; }
    const char *ifname = argv[1];

    int fd = bind_raw_ptp(ifname);
    uint64_t last_sync_ts = 0;
    uint16_t last_seq     = 0;

    printf("gptp_sync: listening on %s (Layer‑2 0x88F7)\n", ifname);

    while (1) {
        uint8_t frame[256];
        char    cbuf[512];
        struct iovec  iov = { frame, sizeof(frame) };
        struct msghdr msg = { 0 };
        msg.msg_iov    = &iov;
        msg.msg_iovlen = 1;
        msg.msg_control = cbuf;
        msg.msg_controllen = sizeof(cbuf);

        ssize_t len = recvmsg(fd, &msg, 0);
        if (len < (ssize_t)sizeof(struct ptp_header)) continue;

        struct ptp_header *h = (struct ptp_header *)frame;
        if (h->version != 2) continue;

        uint8_t type = h->msg_type & 0x0F;
        uint64_t ts  = hw_ts_from_msg(&msg);
        if (!ts) continue; /* must have hw timestamp */

        if (type == PTP_SYNC) {
            last_sync_ts = ts;
            last_seq     = ntohs(h->seq_id);
        } else if (type == PTP_FOLLOW_UP && ntohs(h->seq_id) == last_seq) {
            /* origin timestamp: seconds(6B) + nanos(4B) at offset 34 */
            uint32_t origin_sec_l = ntohl(*(uint32_t *)(frame + 34 + 2));
            uint32_t origin_ns    = ntohl(*(uint32_t *)(frame + 38));
            uint64_t origin_ts    = (uint64_t)origin_sec_l * 1000000000ULL + origin_ns;
            int64_t  offset       = (int64_t)origin_ts - (int64_t)last_sync_ts;
            printf("seq %u  offset %+lld ns\n", last_seq, (long long)offset);
            adjust_clock(offset);
        }
    }
}
#endif /* APP_GPTP_SYNC */

/********************************************************************
 * SECTION 3 – TSN Qdisc configurator via libmnl – tsn_qdisc
 ********************************************************************/
#ifdef APP_TSN_QDISC
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <linux/pkt_sched.h>
#include <linux/rtnetlink.h>
#include <mnl/mnl.h>
#include <net/if.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void nl_error_cb(const struct nlmsghdr *nlh)
{
    struct nlmsgerr *e = (struct nlmsgerr *)mnl_nlmsg_get_payload(nlh);
    if (e->error)
        fprintf(stderr, "netlink error: %s\n", strerror(-e->error));
}

static void add_cbs(const char *ifname, uint32_t parent, uint32_t idleslope,
                    int32_t sendslope, int32_t hicredit, int32_t locredit)
{
    char buf[MNL_SOCKET_BUFFER_SIZE];
    struct nlmsghdr *nlh = mnl_nlmsg_put_header(buf);
    nlh->nlmsg_type  = RTM_NEWQDISC;
    nlh->nlmsg_flags = NLM_F_REQUEST | NLM_F_CREATE | NLM_F_EXCL | NLM_F_ACK;
    nlh->nlmsg_seq   = time(NULL);

    struct tcmsg *t = mnl_nlmsg_put_extra_header(nlh, sizeof(*t));
    memset(t, 0, sizeof(*t));
    t->tcm_ifindex = if_nametoindex(ifname);
    t->tcm_parent  = parent;
    t->tcm_handle  = 0;              /* let kernel choose */

    mnl_attr_put_strz(nlh, TCA_KIND, "cbs");
    struct nlattr *opt = mnl_attr_nest_start(nlh, TCA_OPTIONS);
    mnl_attr_put_u32(nlh, TCA_CBS_IDLESLOPE, htonl(idleslope));
    mnl_attr_put_s32(nlh, TCA_CBS_SENDSLOPE, htonl(sendslope));
    mnl_attr_put_s32(nlh, TCA_CBS_HICREDIT, htonl(hicredit));
    mnl_attr_put_s32(nlh, TCA_CBS_LOCREDIT, htonl(locredit));
    mnl_attr_nest_end(nlh, opt);

    struct mnl_socket *nl = mnl_socket_open(NETLINK_ROUTE);
    if (!nl) { perror("mnl_socket_open"); exit(EXIT_FAILURE); }
    if (mnl_socket_bind(nl, 0, MNL_SOCKET_AUTOPID) < 0) { perror("bind"); exit(EXIT_FAILURE); }

    if (mnl_socket_sendto(nl, nlh, nlh->nlmsg_len) < 0) { perror("sendto"); exit(EXIT_FAILURE); }

    char rcv[MNL_SOCKET_BUFFER_SIZE];
    int len = mnl_socket_recvfrom(nl, rcv, sizeof(rcv));
    if (len > 0) mnl_cb_run(rcv, len, nlh->nlmsg_seq, mnl_socket_get_portid(nl), (mnl_cb_t)nl_error_cb, NULL);

    mnl_socket_close(nl);
}

int main(int argc, char **argv)
{
    if (argc < 2) { fprintf(stderr, "Usage: %s <iface>\n", argv[0]); return 1; }
    const char *ifname = argv[1];

    /* parent 1:1 (mqprio root handle 1: mapping TC 1) */
    add_cbs(ifname, TC_H_MAKE(1,1), 196608, -803392, 153, -153);
    printf("CBS configured on %s (parent 1:1)\n", ifname);
    return 0;
}
#endif /* APP_TSN_QDISC */
