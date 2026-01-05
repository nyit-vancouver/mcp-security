/*
 * eBPF Programs for MCP Security Dynamic Analysis
 *
 * This file contains kernel-space eBPF probes for monitoring:
 * - File system operations (open, read, write, unlink)
 * - Network activities (socket, connect, send, recv)
 * - Process management (execve, fork, clone)
 * - Environment variable access (getenv via uprobe)
 */

#include <uapi/linux/ptrace.h>
#include <linux/sched.h>
#include <linux/fs.h>
#include <linux/socket.h>
#include <linux/in.h>
#include <linux/in6.h>

// Event types for userspace communication
#define EVENT_FILE_OPEN     1
#define EVENT_FILE_READ     2
#define EVENT_FILE_WRITE    3
#define EVENT_FILE_UNLINK   4
#define EVENT_NET_SOCKET    5
#define EVENT_NET_CONNECT   6
#define EVENT_NET_SEND      7
#define EVENT_NET_RECV      8
#define EVENT_PROC_EXEC     9
#define EVENT_PROC_FORK     10
#define EVENT_ENV_ACCESS    11

// Maximum path/command length
#define MAX_PATH_LEN 256
#define MAX_CMD_LEN  128

// Event structure passed to userspace
struct event_data {
    u32 event_type;
    u32 pid;
    u32 uid;
    char comm[TASK_COMM_LEN];
    char path[MAX_PATH_LEN];
    u64 timestamp;
    u64 size;           // File size or network bytes
    u32 flags;          // Open flags or socket type
    u32 fd;             // File descriptor
    u32 addr_family;    // AF_INET, AF_INET6
    u32 port;           // Network port
    u8  ip[16];         // IPv4/IPv6 address
};

// Ring buffer for events
BPF_PERF_OUTPUT(events);

// Helper to read string safely
static inline void read_str_safe(char *dst, const char *src, size_t max_len) {
    bpf_probe_read_user_str(dst, max_len, src);
}

// ============================================================================
// FILE SYSTEM MONITORING
// ============================================================================

// Hook: open/openat syscall entry
int trace_open_entry(struct pt_regs *ctx, int dfd, const char __user *filename, int flags) {
    struct event_data event = {};
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u64 uid_gid = bpf_get_current_uid_gid();

    event.event_type = EVENT_FILE_OPEN;
    event.pid = pid_tgid >> 32;
    event.uid = uid_gid & 0xFFFFFFFF;
    event.timestamp = bpf_ktime_get_ns();
    event.flags = flags;

    bpf_get_current_comm(&event.comm, sizeof(event.comm));
    bpf_probe_read_user_str(event.path, sizeof(event.path), filename);

    events.perf_submit(ctx, &event, sizeof(event));
    return 0;
}

// Hook: read syscall
int trace_read_entry(struct pt_regs *ctx, unsigned int fd, char __user *buf, size_t count) {
    struct event_data event = {};
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u64 uid_gid = bpf_get_current_uid_gid();

    event.event_type = EVENT_FILE_READ;
    event.pid = pid_tgid >> 32;
    event.uid = uid_gid & 0xFFFFFFFF;
    event.timestamp = bpf_ktime_get_ns();
    event.fd = fd;
    event.size = count;

    bpf_get_current_comm(&event.comm, sizeof(event.comm));

    events.perf_submit(ctx, &event, sizeof(event));
    return 0;
}

// Hook: write syscall
int trace_write_entry(struct pt_regs *ctx, unsigned int fd, const char __user *buf, size_t count) {
    struct event_data event = {};
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u64 uid_gid = bpf_get_current_uid_gid();

    event.event_type = EVENT_FILE_WRITE;
    event.pid = pid_tgid >> 32;
    event.uid = uid_gid & 0xFFFFFFFF;
    event.timestamp = bpf_ktime_get_ns();
    event.fd = fd;
    event.size = count;

    bpf_get_current_comm(&event.comm, sizeof(event.comm));

    events.perf_submit(ctx, &event, sizeof(event));
    return 0;
}

// Hook: unlink/unlinkat syscall
int trace_unlink_entry(struct pt_regs *ctx, const char __user *pathname) {
    struct event_data event = {};
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u64 uid_gid = bpf_get_current_uid_gid();

    event.event_type = EVENT_FILE_UNLINK;
    event.pid = pid_tgid >> 32;
    event.uid = uid_gid & 0xFFFFFFFF;
    event.timestamp = bpf_ktime_get_ns();

    bpf_get_current_comm(&event.comm, sizeof(event.comm));
    bpf_probe_read_user_str(event.path, sizeof(event.path), pathname);

    events.perf_submit(ctx, &event, sizeof(event));
    return 0;
}

// ============================================================================
// NETWORK MONITORING
// ============================================================================

// Hook: socket syscall
int trace_socket_entry(struct pt_regs *ctx, int family, int type, int protocol) {
    struct event_data event = {};
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u64 uid_gid = bpf_get_current_uid_gid();

    event.event_type = EVENT_NET_SOCKET;
    event.pid = pid_tgid >> 32;
    event.uid = uid_gid & 0xFFFFFFFF;
    event.timestamp = bpf_ktime_get_ns();
    event.addr_family = family;
    event.flags = type;

    bpf_get_current_comm(&event.comm, sizeof(event.comm));

    events.perf_submit(ctx, &event, sizeof(event));
    return 0;
}

// Hook: connect syscall
int trace_connect_entry(struct pt_regs *ctx, int fd, struct sockaddr __user *uaddr, int addrlen) {
    struct event_data event = {};
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u64 uid_gid = bpf_get_current_uid_gid();

    event.event_type = EVENT_NET_CONNECT;
    event.pid = pid_tgid >> 32;
    event.uid = uid_gid & 0xFFFFFFFF;
    event.timestamp = bpf_ktime_get_ns();
    event.fd = fd;

    bpf_get_current_comm(&event.comm, sizeof(event.comm));

    // Read socket address
    struct sockaddr sa;
    bpf_probe_read_user(&sa, sizeof(sa), uaddr);
    event.addr_family = sa.sa_family;

    if (sa.sa_family == AF_INET) {
        struct sockaddr_in *sin = (struct sockaddr_in *)&sa;
        event.port = __builtin_bswap16(sin->sin_port);
        bpf_probe_read_user(&event.ip, 4, &sin->sin_addr);
    } else if (sa.sa_family == AF_INET6) {
        struct sockaddr_in6 *sin6 = (struct sockaddr_in6 *)&sa;
        event.port = __builtin_bswap16(sin6->sin6_port);
        bpf_probe_read_user(&event.ip, 16, &sin6->sin6_addr);
    }

    events.perf_submit(ctx, &event, sizeof(event));
    return 0;
}

// Hook: sendto syscall
int trace_sendto_entry(struct pt_regs *ctx, int fd, void __user *buff, size_t len) {
    struct event_data event = {};
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u64 uid_gid = bpf_get_current_uid_gid();

    event.event_type = EVENT_NET_SEND;
    event.pid = pid_tgid >> 32;
    event.uid = uid_gid & 0xFFFFFFFF;
    event.timestamp = bpf_ktime_get_ns();
    event.fd = fd;
    event.size = len;

    bpf_get_current_comm(&event.comm, sizeof(event.comm));

    events.perf_submit(ctx, &event, sizeof(event));
    return 0;
}

// Hook: recvfrom syscall
int trace_recvfrom_entry(struct pt_regs *ctx, int fd, void __user *ubuf, size_t size) {
    struct event_data event = {};
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u64 uid_gid = bpf_get_current_uid_gid();

    event.event_type = EVENT_NET_RECV;
    event.pid = pid_tgid >> 32;
    event.uid = uid_gid & 0xFFFFFFFF;
    event.timestamp = bpf_ktime_get_ns();
    event.fd = fd;
    event.size = size;

    bpf_get_current_comm(&event.comm, sizeof(event.comm));

    events.perf_submit(ctx, &event, sizeof(event));
    return 0;
}

// ============================================================================
// PROCESS MONITORING
// ============================================================================

// Hook: execve syscall
int trace_execve_entry(struct pt_regs *ctx, const char __user *filename,
                       const char __user *const __user *argv) {
    struct event_data event = {};
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u64 uid_gid = bpf_get_current_uid_gid();

    event.event_type = EVENT_PROC_EXEC;
    event.pid = pid_tgid >> 32;
    event.uid = uid_gid & 0xFFFFFFFF;
    event.timestamp = bpf_ktime_get_ns();

    bpf_get_current_comm(&event.comm, sizeof(event.comm));
    bpf_probe_read_user_str(event.path, sizeof(event.path), filename);

    events.perf_submit(ctx, &event, sizeof(event));
    return 0;
}

// Hook: fork/clone syscall
int trace_fork_entry(struct pt_regs *ctx) {
    struct event_data event = {};
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u64 uid_gid = bpf_get_current_uid_gid();

    event.event_type = EVENT_PROC_FORK;
    event.pid = pid_tgid >> 32;
    event.uid = uid_gid & 0xFFFFFFFF;
    event.timestamp = bpf_ktime_get_ns();

    bpf_get_current_comm(&event.comm, sizeof(event.comm));

    events.perf_submit(ctx, &event, sizeof(event));
    return 0;
}
