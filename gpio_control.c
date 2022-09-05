#define RASPBIAN_HACK

/* gpio_control.c

   =======================================================================
   Update:  2014.11.01

   Raspbian OS export operation now assigns group "gpio" to the created GPIO files.
   This gpio_control program now writes informational messages to stdout to
   report what is required for the current user to use the newly-created GPIO files.
   ======================================================================= 

   Arguments:  pin_number  export|unexport

   Export or unexport the specified GPIO pin.  Set group ownership and permissions
   for the relevent GPIO files that a successful export creates.


   INSTALLATION

   This program must run with root privilege, but normally will be invoked
   by ordinary users.  To compile the program (no special privilege is required):

     gcc -g -O2 -o gpio_control gpio_control.c

   This produces the binary executable file:  gpio_control

   This file should be copied by root into a system directory such as
   /usr/sbin using:

     sudo cp gpio_control /usr/sbin/

   (therefore the owner of the file will be root).  Then, the "setuid"
   attribute should be set by the command:

     sudo chmod u+s /usr/sbin/gpio_control

*/


/* Exactly 54 pins, denoted 0-53, are implemented by the Broadcom BCM2835
   used in the Raspberry Pi. */
#define pin_max    53

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <ctype.h>
#include <grp.h>
#include <pwd.h>

#include <sys/types.h>
#include <sys/stat.h>

/* Array to define which GPIO pins may be exported.
   Specify 0 for a pin to forbid export and use of that pin;
   specify 1 to allow access. */

static const unsigned char allowed_pins[] =
  { 1,         /* Pin  0 */
    1,         /* Pin  1 */
    1,         /* Pin  2 */
    1,         /* Pin  3 */
    1,         /* Pin  4 */
    1,         /* Pin  5 */
    1,         /* Pin  6 */
    1,         /* Pin  7 */
    1,         /* Pin  8 */
    1,         /* Pin  9 */
    1,         /* Pin 10 */
    1,         /* Pin 11 */
    1,         /* Pin 12 */
    1,         /* Pin 13 */
    1,         /* Pin 14 */
    1,         /* Pin 15 */
    1,         /* Pin 16 */
    1,         /* Pin 17 */
    1,         /* Pin 18 */
    1,         /* Pin 19 */
    1,         /* Pin 20 */
    1,         /* Pin 21 */
    1,         /* Pin 22 */
    1,         /* Pin 23 */
    1,         /* Pin 24 */
    1,         /* Pin 25 */
    1,         /* Pin 26 */
    1,         /* Pin 27 */
    1,         /* Pin 28 */
    1,         /* Pin 29 */
    1,         /* Pin 30 */
    1,         /* Pin 31 */
    1,         /* Pin 32 */
    1,         /* Pin 33 */
    1,         /* Pin 34 */
    1,         /* Pin 35 */
    1,         /* Pin 36 */
    1,         /* Pin 37 */
    1,         /* Pin 38 */
    1,         /* Pin 39 */
    1,         /* Pin 40 */
    1,         /* Pin 41 */
    1,         /* Pin 42 */
    1,         /* Pin 43 */
    1,         /* Pin 44 */
    1,         /* Pin 45 */
    1,         /* Pin 46 */
    1,         /* Pin 47 */
    1,         /* Pin 48 */
    1,         /* Pin 49 */
    1,         /* Pin 50 */
    1,         /* Pin 51 */
    1,         /* Pin 52 */
    1,         /* Pin 53 */
  };


static void drop_privilege()
{setuid(getuid());  /* Irrevocably drop all privilege obtained by set-user-ID-root */
}


/* 
   getpwuid and getgrgid use static buffers.  Do not call a second time
   until the first call's results have been copied, because tho previous results will be
   updated by the second call.  Because uname_from_uid and gname_from_gid use these functions,
   the same usage applies here, too.
 */

static char * uname_from_uid (uid_t uid) {
  struct passwd  *pws;
  pws = getpwuid(uid);
  if (pws != NULL) return pws->pw_name;
  else return "<invalid uid>";
}

static char * gname_from_gid (gid_t gid) {
  struct group  *gs;
  gs = getgrgid(gid);
  if (gs != NULL) {
    return gs->gr_name;}
  else return "<invalid gid>";
}



static int check_uid_in_gid (uid_t uid, gid_t gid) {
  /* Returns 1 if user ID uid is a member of the group denoted by
     group ID gid; otherwise returns 0 . */
  struct group    *gs;
  struct passwd  *pws;
  char  **name_vector;

  gs = getgrgid(gid);
  if (! gs) return 0;      /* Unknown group. */

  pws = getpwuid(uid);
  if (! pws) return 0;     /* Unknown user. */

  name_vector = gs->gr_mem;
  while (*name_vector) {
    if (strcmp(*name_vector, pws->pw_name) == 0)
      return 1;
    name_vector++;
  }
  return 0;
}


static int change_mode (char *pin, char *fname, gid_t gid)
  {
  char            path_buff[64];
  int                    rc;
  mode_t               mode;  

  if (fname[0] == 0)   /* Empty name; apply to this pin's directory. */
    sprintf(path_buff, "/sys/class/gpio/gpio%s", pin);
  else
    sprintf(path_buff, "/sys/class/gpio/gpio%s/%s", pin, fname);

  mode =  S_IWGRP | S_IRGRP | S_IWUSR | S_IRUSR;
  if (fname[0] == 0) { 
    mode |=  S_IXGRP | S_IXUSR;   /* Add execute permission to the pin directory. */
  }

  rc = chmod(path_buff, mode);
  if (rc)
    {
      perror(path_buff);
      return rc;
    }
  rc = chown(path_buff, -1, gid);
  if (rc)
    perror("chown failed");
  return 0;
  }





int main (int argc, char **argv)
{
  int                     x, fd, exit_code, pin_number;
  char             *path_ex = "/sys/class/gpio/export";
  char             *path_un = "/sys/class/gpio/unexport";
  char            path_buff[64];

  char             pin_buff[5];
  char             msg_buff[256];
  gid_t                 gid;
  struct stat   stat_buffer;
  struct group       *group;

  if (argc < 3)
    {
      drop_privilege();
      fprintf(stderr, "%s requires two arguments:\n1:  GPIO pin number\n2:  Operation (export or unexport)\nPin number specifies one of the 54 Broadcom BCM2835 GPIO pins.\n", argv[0]);
      return 1;
    }

   /* Make a local copy of pin number argument, and test it is a number. */
  for (x=0; x<sizeof(pin_buff); x++)
    {
      pin_buff[x] = argv[1][x];
      if (! isdigit(pin_buff[x])) break;
    }
  if (pin_buff[x] != 0)
    {
      drop_privilege();
      fprintf(stderr, "Invalid pin number format.\n");
      return 1;
    }
  sscanf(pin_buff, "%d", &pin_number);  /* Get binary pin number. */
  if (pin_number > pin_max)
    {
      drop_privilege();
      fprintf(stderr, "Pin number must be less than %d\n", pin_max);
      return 1;
    }
  if (allowed_pins[pin_number] == 0)
    {
      drop_privilege();
      fprintf(stderr, "Pin %d is not configured for user access.\n", pin_number);
      return 4;
    }

  gid = getegid();
  if (0 == strcmp(argv[2], "unexport")) {

    /* Check group owner of the exported pin's files.  Fail if it does not
       maatch the current user's group. */

    if (gid != 0) {
      sprintf(path_buff, "/sys/class/gpio/gpio%s", pin_buff);    
      x = stat(path_buff, &stat_buffer);     /* Get file attributes of GPIO files.. */
      if (x != 0) {
	fprintf(stderr, "GPIO pin %s is not currently exported.\n", pin_buff);
	return 3;
      }

      if (stat_buffer.st_gid != gid) {  /* Some other user has this pin. */
	drop_privilege();
	x = sprintf(msg_buff, "%s not permitted to unexport GPIO pin %s, used by ", gname_from_gid(gid), pin_buff);
	x += sprintf(msg_buff + x, "%s.", gname_from_gid(stat_buffer.st_gid));
	fprintf(stderr, "%s\n", msg_buff);
	return 3;
      }
    }

    fd = open(path_un, O_WRONLY);
    if (fd < 0)
      {
	perror(path_un);
	return 2;
      }
    if (0 > write(fd, pin_buff, strlen(pin_buff)))
      {
	perror("unexport failed");
	exit_code = 3;
      }
    return 0;
  }


  if (0 == strcmp(argv[2], "export"))  {
    fd = open(path_ex, O_WRONLY);
    if (fd < 0)
      {
	perror(path_ex);
	return 2;
      }
    if (0 > write(fd, pin_buff, strlen(pin_buff)))
      {
	perror("export failed");
	close(fd);
	return 3;
      }
    close(fd);
    exit_code = 0;
  
    /* Set ownership (group) and permissions of the new GPIO files. */

    if (gid != 0) {

#ifdef RASPBIAN_HACK
      /* Raspbian made a sloppy change to kernel GPIO export semantics:
	   https://github.com/raspberrypi/linux/issues/553

	   Check for Raspbian OS.
      */
      if (0 == stat("/etc/dpkg/origins/raspbian", &stat_buffer))
	/* OK, OS seems to be Raspbian. */

	sleep(1);           /* Ugly hack to allow GPIO file metadata to stabilize 
			       so that the following mode changes are not over-written.

			       This is only a palliative; there is no way to know
			       how long the user space process will take to set permissions
			       on the files created by Raspbian's GPIO export operation.. */
#endif

      exit_code |= change_mode(pin_buff, "active_low", gid);
      exit_code |= change_mode(pin_buff, "direction", gid);
      exit_code |= change_mode(pin_buff, "edge", gid);
      exit_code |= change_mode(pin_buff, "value", gid);
      exit_code |= change_mode(pin_buff, "", gid);
    }
    close(fd);    /* This removes the lock. */
    return exit_code;
  }

/* Request is neither export nor unexport.*/

  drop_privilege();
  fprintf(stderr, "Argument 2 must be either \"export\" or \"unexport\".\n");
  return 1;
}
