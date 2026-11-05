import java.util.*;
import infodynamics.measures.continuous.kraskov.*;

/** Application loading only: official JIDT estimator and neighbour algorithms unchanged. */
public final class ElapsedHourLoader {
  private ElapsedHourLoader() {}
  public static void validate(int[] hours, double[][]... arrays) {
    if(hours.length==0) throw new IllegalArgumentException("No observations");
    for(int i=0;i<hours.length;i++) if(hours[i]<0 || (i>0 && hours[i]<=hours[i-1]))
      throw new IllegalArgumentException("Require increasing nonnegative elapsed-hour indices");
    for(double[][] a:arrays) {
      if(a.length!=hours.length || a[0].length==0) throw new IllegalArgumentException("Array/time mismatch");
      int d=a[0].length;
      for(double[] row:a) {if(row.length!=d) throw new IllegalArgumentException("Ragged array"); for(double v:row)if(!Double.isFinite(v)) throw new IllegalArgumentException("Nonfinite data");}
    }
  }
  public static void verify(int[] expected, int[] actualTimes, int[] actualSets, int n) {
    if(n!=expected.length || !Arrays.equals(expected,actualTimes) || actualSets.length!=n)
      throw new IllegalStateException("JIDT lost observations or elapsed-time indices");
    for(int id:actualSets) if(id!=0) throw new IllegalStateException("A site's segments must share set ID 0");
  }
  public static void load(MutualInfoCalculatorMultiVariateKraskov1 c,int[] hours,double[][] x,double[][] y,int k,int window) throws Exception {
    validate(hours,x,y); if(k<1||window<0)throw new IllegalArgumentException("Invalid settings");
    c.setProperty("k",""+k);c.setProperty("DYN_CORR_EXCL",""+window);c.setProperty("USE_GPU","false");
    c.setProperty("TIME_DIFF","0");c.initialise(x[0].length,y[0].length);c.startAddObservations();
    for(int start=0;start<hours.length;) {
      int stop=start+1;while(stop<hours.length&&hours[stop]==hours[stop-1]+1)stop++;
      c.addObservationsTrackObservationIDs(Arrays.copyOfRange(x,start,stop),Arrays.copyOfRange(y,start,stop),0,hours[start]);start=stop;
    }
    c.finaliseAddObservations();verify(hours,c.getObservationTimePoints(),c.getObservationSetIndices(),c.getNumObservations());
    if(!c.getProperty("k").equals(""+k)||!c.getProperty("DYN_CORR_EXCL").equals(""+window))throw new IllegalStateException("Java settings mismatch");
  }
  public static void load(ConditionalMutualInfoCalculatorMultiVariateKraskov1 c,int[] hours,double[][] x,double[][] y,double[][] z,int k,int window) throws Exception {
    validate(hours,x,y,z);if(k<1||window<0)throw new IllegalArgumentException("Invalid settings");
    c.setProperty("k",""+k);c.setProperty("DYN_CORR_EXCL",""+window);c.setProperty("USE_GPU","false");
    c.initialise(x[0].length,y[0].length,z[0].length);c.startAddObservations();
    for(int start=0;start<hours.length;) {
      int stop=start+1;while(stop<hours.length&&hours[stop]==hours[stop-1]+1)stop++;
      c.addObservationsTrackObservationIDs(Arrays.copyOfRange(x,start,stop),Arrays.copyOfRange(y,start,stop),Arrays.copyOfRange(z,start,stop),0,hours[start]);start=stop;
    }
    c.finaliseAddObservations();verify(hours,c.getObservationTimePoints(),c.getObservationSetIndices(),c.getNumObservations());
    if(!c.getProperty("k").equals(""+k)||!c.getProperty("DYN_CORR_EXCL").equals(""+window))throw new IllegalStateException("Java settings mismatch");
  }
}
