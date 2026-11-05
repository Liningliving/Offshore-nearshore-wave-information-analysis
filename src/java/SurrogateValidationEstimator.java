import java.io.*;
import java.nio.file.*;
import java.util.*;
import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

/** Application-level surrogate reloads; uses unmodified Step 7 calculators/settings. */
public class SurrogateValidationEstimator {
  static class MI extends MutualInfoCalculatorMultiVariateKraskov1 {
    void verifyNeighbours(int[] t)throws Exception{ensureKdTreesConstructed();for(int i=0;i<t.length;i+=Math.max(1,t.length/20))for(NeighbourNodeData p:kdTreeJoint.findKNearestNeighbours(4,i,45))if(Math.abs(t[i]-t[p.sampleIndex])<=45)throw new AssertionError("MI neighbour within 45 h");}
  }
  static class CMI extends ConditionalMutualInfoCalculatorMultiVariateKraskov1 {
    void verifyNeighbours(int[] t)throws Exception{ensureKdTreesConstructed();for(int i=0;i<t.length;i+=Math.max(1,t.length/20))for(NeighbourNodeData p:kdTreeJoint.findKNearestNeighbours(4,i,45))if(Math.abs(t[i]-t[p.sampleIndex])<=45)throw new AssertionError("CMI neighbour within 45 h");}
  }
  public static void main(String[] args)throws Exception{
    // manifest: data CSV, orders CSV, output CSV, measure (mi/period/direction)
    for(String job:Files.readAllLines(Path.of(args[0]))){
      String[] fields=job.split("\t");List<String> rows=Files.readAllLines(Path.of(fields[0]));int n=rows.size();int[] hours=new int[n];double[][] values=new double[n][5];
      for(int i=0;i<n;i++){String[] a=rows.get(i).split(",");hours[i]=Integer.parseInt(a[0]);for(int j=0;j<5;j++)values[i][j]=Double.parseDouble(a[j+1]);}
      boolean mi=fields[3].equals("mi"),direction=fields[3].equals("direction");
      List<String> orders=Files.readAllLines(Path.of(fields[1]));
      try(PrintWriter out=new PrintWriter(fields[2])){
        out.println("draw,nats,bits,observations,timing_verified,nearest_neighbours_verified");
        for(int draw=-1;draw<orders.size();draw++){
          String[] map=draw<0?null:orders.get(draw).split(",");if(map!=null&&map.length!=n)throw new IllegalArgumentException("Wrong order size");
          double[][] x=new double[n][direction?2:1],y=new double[n][1],z=new double[n][1];
          for(int i=0;i<n;i++){int j=draw<0?i:Integer.parseInt(map[i]);x[i][0]=values[j][mi?0:direction?3:2];if(direction)x[i][1]=values[j][4];y[i][0]=values[i][1];z[i][0]=values[i][0];}
          double estimate;
          if(mi){MI c=new MI();SharedEstimatorSettings.apply(c);ElapsedHourLoader.load(c,hours,x,y,4,45);SharedEstimatorSettings.verify(c);c.verifyNeighbours(hours);estimate=c.computeAverageLocalOfObservations();}
          else{CMI c=new CMI();SharedEstimatorSettings.apply(c);ElapsedHourLoader.load(c,hours,x,y,z,4,45);SharedEstimatorSettings.verify(c);c.verifyNeighbours(hours);estimate=c.computeAverageLocalOfObservations();}
          out.printf(Locale.ROOT,"%d,%.17g,%.17g,%d,true,true%n",draw,estimate,estimate/Math.log(2),n);
        }
      }
      System.out.println(fields[3]+" "+fields[2]+" N="+n+" B="+orders.size());
    }
  }
}
